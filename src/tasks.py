"""
Celery Background Tasks
Long-running tasks that should not block the main request thread.
"""
from .celery_app import celery_app
from .utils import setup_logging
import tempfile
from pathlib import Path

logger = setup_logging()


@celery_app.task(
    name='src.tasks.scrape_and_embed_url',
    bind=True
    # Time limits are set in celery_app.py via task_annotations to avoid conflicts
)
def scrape_and_embed_url_task(self, url: str, collection_name: str = None, 
                               version: str = None, overwrite: bool = False, 
                               max_depth: int = 3):
    """
    Background task to scrape a URL and embed the content.
    
    Args:
        url: Starting URL to scrape
        collection_name: Optional collection name
        version: Optional version string
        overwrite: Whether to overwrite existing collection
        max_depth: Maximum crawl depth
        
    Returns:
        dict: Results with success count, failed count, errors, and pages
    """
    try:
        from .web_scraper import WebScraper
        from .embed import embed_file
        
        logger.info(f"Starting background scraping task for URL: {url}")
        
        # Update task state - starting
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Starting web scraping', 'url': url, 'progress': 0}
        )
        
        # Step 1: Scrape URLs with progress updates
        scraper = WebScraper(max_depth=max_depth)
        
        # Modify scraper to report progress by wrapping _fetch_page
        original_fetch = scraper._fetch_page
        scraped_count = [0]  # Use list for mutable counter
        
        def fetch_with_progress(fetch_url: str):
            """Wrapper to update progress during scraping."""
            result = original_fetch(fetch_url)
            if result:
                scraped_count[0] += 1
                # Update progress: 0-10% for scraping phase
                # Estimate based on pages scraped (assume ~50-200 pages for typical site)
                estimated_total = 100  # Conservative estimate
                progress = min(10, int((scraped_count[0] / estimated_total) * 10))
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Scraping page {scraped_count[0]}: {fetch_url[:50]}...',
                        'url': fetch_url,
                        'progress': progress
                    }
                )
            return result
        
        scraper._fetch_page = fetch_with_progress
        scraped_pages = scraper.scrape_url(url)
        
        if not scraped_pages:
            raise ValueError(f"No content found at {url}")
        
        total_pages = len(scraped_pages)
        logger.info(f"Scraped {total_pages} pages. Starting embedding process...")
        
        # Update task state - scraping complete, starting embedding
        self.update_state(
            state='PROGRESS',
            meta={
                'status': f'Scraping completed. Embedding {total_pages} pages...',
                'url': url,
                'progress': 10  # 10% - scraping done
            }
        )
        
        # Step 2: Embed each page with progress updates
        success_count = 0
        failed_pages = []
        pages_results = []
        
        # Create temporary directory for scraped content
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            for i, page in enumerate(scraped_pages):
                page_url = page['url']
                page_title = page['title']
                page_content = page['content']
                
                # Calculate progress: 10% (scraping) + 90% (embedding)
                progress = 10 + int((i / total_pages) * 90)
                
                # Check if task has been revoked/cancelled - only check periodically to avoid overhead
                # Check every 10 pages or on first/last page
                should_check_cancellation = (i % 10 == 0) or (i == 0) or (i == total_pages - 1)
                
                if should_check_cancellation:
                    # Check if task has been revoked/cancelled
                    # For bound tasks, we can check self.request.revoked (lightweight check)
                    if hasattr(self.request, 'revoked') and self.request.revoked:
                        logger.info(f"Task cancelled by user. Processed {i}/{total_pages} pages before cancellation.")
                        self.update_state(
                            state='REVOKED',
                            meta={'status': 'Cancelled', 'progress': progress, 'url': url}
                        )
                        return {
                            'status': 'cancelled',
                            'message': f'Task cancelled. Processed {i}/{total_pages} pages.',
                            'results': {
                                'success': success_count,
                                'failed': len(failed_pages),
                                'errors': failed_pages,
                                'pages': pages_results
                            }
                        }
                    
                    # Also check task state using AsyncResult (more expensive, so only periodically)
                    # This is more reliable as it checks the actual task state in the backend
                    try:
                        from celery.result import AsyncResult
                        task_result = AsyncResult(self.request.id, app=self.app)
                        if task_result.state == 'REVOKED':
                            logger.info(f"Task cancelled by user. Processed {i}/{total_pages} pages before cancellation.")
                            self.update_state(
                                state='REVOKED',
                                meta={'status': 'Cancelled', 'progress': progress, 'url': url}
                            )
                            return {
                                'status': 'cancelled',
                                'message': f'Task cancelled. Processed {i}/{total_pages} pages.',
                                'results': {
                                    'success': success_count,
                                    'failed': len(failed_pages),
                                    'errors': failed_pages,
                                    'pages': pages_results
                                }
                            }
                    except Exception as e:
                        # If checking state fails, continue processing
                        logger.debug(f"Could not check task revocation state: {e}")
                
                # Update task state with current page being processed
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Embedding page {i+1}/{total_pages}: {page_title}',
                        'url': page_url,
                        'progress': progress
                    }
                )
                
                logger.info(f"Embedding page {i+1}/{total_pages}: {page_url} ({page_title})")
                
                try:
                    # Save content to a temporary file
                    temp_file_path = tmp_path / f"scraped_page_{i}.md"
                    temp_file_path.write_text(f"# {page_title}\n\n{page_content}")
                    
                    # Embed the temporary file
                    embed_file(
                        str(temp_file_path),
                        collection_name=collection_name,
                        version=version,
                        overwrite=overwrite if i == 0 else False  # Overwrite only for first file
                    )
                    success_count += 1
                    pages_results.append({
                        'url': page_url,
                        'title': page_title,
                        'status': 'success'
                    })
                    logger.info(f"Successfully embedded page {i+1}/{total_pages}: {page_url}")
                    
                except Exception as e:
                    logger.error(f"Failed to embed scraped page {page_url}: {e}")
                    failed_pages.append({'url': page_url, 'error': str(e)})
                    pages_results.append({
                        'url': page_url,
                        'title': page_title,
                        'status': 'failed'
                    })
        
        # Final update - completed
        self.update_state(
            state='PROGRESS',
            meta={
                'status': f'Completed: {success_count} pages embedded successfully',
                'url': url,
                'progress': 100
            }
        )
        
        results = {
            'success': success_count,
            'failed': len(failed_pages),
            'errors': failed_pages,
            'pages': pages_results
        }
        
        logger.info(f"Background scraping completed for URL: {url}. "
                   f"Success: {success_count}, Failed: {len(failed_pages)}")
        
        return {
            'status': 'completed',
            'results': results,
            'version': version,
            'collection_name': collection_name
        }
        
    except Exception as e:
        logger.error(f"Background scraping task failed for URL {url}: {e}", exc_info=True)
        self.update_state(
            state='FAILURE',
            meta={'status': 'Failed', 'error': str(e), 'url': url}
        )
        raise


# RAG System Web UI

Modern Angular web interface for the RAG System.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8080` (or configure in environment)

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm start

# Access at http://localhost:4200
```

### Building for Production

```bash
# Build the application
npm run build

# Output will be in dist/ directory
# Serve the dist/ folder from your web server or backend
```

## 🏗️ Architecture

The web UI is built with **Angular 19** using standalone components and signals for state management.

### Project Structure

```
web-ui/src/app/
├── features/              # Feature modules
│   ├── admin/             # Admin features
│   │   ├── dashboard/     # Dashboard
│   │   ├── import/        # Upload & Import
│   │   ├── collections/   # Collections
│   │   ├── monitoring/    # Monitoring
│   │   └── settings/      # Settings
│   ├── query/             # Query interface
│   └── auth/              # Authentication
├── core/                   # Core services and state
│   ├── services/          # API services
│   ├── state/             # State management
│   └── models/            # Data models
├── layout/                # Layout components
│   ├── header/            # Header
│   ├── navigation/        # Sidebar
│   └── footer/            # Footer
└── shared/                # Shared components
```

### Key Technologies

- **Angular 19** - Framework
- **Signals** - Reactive state management
- **Tailwind CSS** - Styling
- **RxJS** - Async operations
- **Standalone Components** - No NgModules

## 📝 Development

### Running in Development

```bash
npm start
```

The app will automatically reload when you change any source files.

### Code Generation

```bash
# Generate a new component
ng generate component component-name

# Generate a new service
ng generate service service-name
```

### Testing

```bash
# Run unit tests
npm test

# Run end-to-end tests
npm run e2e
```

## ⚙️ Configuration

### Environment Configuration

Edit `src/environments/environment.ts`:

```typescript
export const environment = {
  apiUrl: 'http://localhost:8080'  // Backend API URL
};
```

### API Integration

The web UI communicates with the backend via REST API. All API calls are handled through services in `core/services/`:

- `ApiService` - Base API service with authentication
- `EmbedService` - Document embedding and Confluence import
- `QueryService` - Query operations
- `CollectionService` - Collection management
- `SettingsService` - Settings management

## 🎨 Features

### Pages

- **Query** - Natural language querying with version selection
- **History** - Query history with search and rerun
- **Dashboard** - System overview and quick actions
- **Upload & Import** - Document upload and Confluence import
- **Collections** - Collection management
- **Monitoring** - System statistics and analytics
- **Settings** - System, Confluence, and LLM provider configuration

### Key Features

- Modern, responsive UI
- Real-time feedback and loading states
- Helpful tooltips and icons
- Error handling with user-friendly messages
- Session-based authentication
- Version-aware operations

## 🔧 Building

### Development Build

```bash
npm run build
```

### Production Build

```bash
npm run build --configuration production
```

The build artifacts will be stored in the `dist/` directory.

## 📚 Documentation

For more information:

- [Main README](../README.md) - Complete system documentation
- [Developer Guide](../docs/DEVELOPER_GUIDE.md) - Architecture details
- [API Reference](../docs/API_REFERENCE.md) - Backend API documentation

## 🐛 Troubleshooting

**Build errors?**
- Clear node_modules and reinstall: `rm -rf node_modules package-lock.json && npm install`
- Check Node.js version: `node --version` (requires 18+)

**API connection issues?**
- Verify backend is running on configured port
- Check CORS settings in backend
- Verify API URL in environment configuration

**Styling issues?**
- Ensure Tailwind CSS is properly configured
- Check that styles are imported in `angular.json`

---

For backend setup and API documentation, see the [main README](../README.md).

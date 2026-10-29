import React, { Component, ErrorInfo, ReactNode } from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Targon Frontend Uncaught Error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#FBFBFD',
          fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif',
          padding: '2rem',
          textAlign: 'center',
          color: '#1D1D1F'
        }}>
          <div style={{
            background: 'white',
            borderRadius: '24px',
            padding: '2.5rem',
            boxShadow: '0 20px 40px rgba(0,0,0,0.08)',
            maxWidth: '560px',
            width: '100%',
            border: '1px solid rgba(0,0,0,0.08)'
          }}>
            <h1 style={{ fontSize: '22px', fontWeight: 700, margin: '0 0 12px 0' }}>
              Targon Encountered an Error
            </h1>
            <p style={{ color: '#86868B', fontSize: '14px', lineHeight: 1.5, marginBottom: '20px' }}>
              {this.state.error?.message || 'An unexpected rendering error occurred.'}
            </p>
            <pre style={{
              background: '#F5F5F7',
              borderRadius: '12px',
              padding: '12px',
              fontSize: '11px',
              textAlign: 'left',
              overflow: 'auto',
              maxHeight: '160px',
              color: '#E03E3E'
            }}>
              {this.state.error?.stack}
            </pre>
            <button
              onClick={() => window.location.reload()}
              style={{
                marginTop: '20px',
                padding: '10px 24px',
                borderRadius: '12px',
                backgroundColor: '#0071E3',
                color: 'white',
                border: 'none',
                fontWeight: 600,
                fontSize: '14px',
                cursor: 'pointer'
              }}
            >
              Reload Application
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);

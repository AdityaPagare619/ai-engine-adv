import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '../store/store';
import ProtectedRoute from '../components/common/ProtectedRoute';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorBoundary from '../components/common/ErrorBoundary';

// Lazy loading for code splitting
const LoginPage = lazy(() => import('../components/auth/LoginPage'));
const DashboardPage = lazy(() => import('../components/dashboard/DashboardPage'));
const ExamListPage = lazy(() => import('../components/exams/ExamListPage'));
const ExamTakePage = lazy(() => import('../components/exams/ExamTakePage'));
const ExamResultsPage = lazy(() => import('../components/exams/ExamResultsPage'));
const QuestionBankPage = lazy(() => import('../components/questions/QuestionBankPage'));
const QuestionDetailPage = lazy(() => import('../components/questions/QuestionDetailPage'));
const CreateQuestionPage = lazy(() => import('../components/questions/CreateQuestionPage'));
const ProfilePage = lazy(() => import('../components/profile/ProfilePage'));
const AdminDashboard = lazy(() => import('../components/admin/AdminDashboard'));
const UserManagement = lazy(() => import('../components/admin/UserManagement'));
const AnalyticsPage = lazy(() => import('../components/analytics/AnalyticsPage'));
const SettingsPage = lazy(() => import('../components/settings/SettingsPage'));
const HelpPage = lazy(() => import('../components/help/HelpPage'));
const NotFoundPage = lazy(() => import('../components/common/NotFoundPage'));

// Custom hook for route tracking and analytics
const useRouteTracking = () => {
  const location = useLocation();
  const user = useSelector((state: RootState) => state.auth.user);

  React.useEffect(() => {
    // Track route changes for analytics
    if (user && typeof window !== 'undefined' && window.gtag) {
      window.gtag('config', process.env.REACT_APP_GA_TRACKING_ID, {
        page_title: document.title,
        page_location: window.location.href,
        user_id: user.id,
      });
    }
  }, [location, user]);
};

// Route configuration for better maintainability
interface RouteConfig {
  path: string;
  element: React.ComponentType;
  requiresAuth: boolean;
  allowedRoles?: string[];
  title: string;
  description?: string;
}

const routeConfigs: RouteConfig[] = [
  {
    path: '/login',
    element: LoginPage,
    requiresAuth: false,
    title: 'Login - JEE AI Platform',
  },
  {
    path: '/dashboard',
    element: DashboardPage,
    requiresAuth: true,
    title: 'Dashboard - JEE AI Platform',
    description: 'Your personalized learning dashboard',
  },
  {
    path: '/exams',
    element: ExamListPage,
    requiresAuth: true,
    title: 'Exams - JEE AI Platform',
    description: 'Browse and take practice exams',
  },
  {
    path: '/exams/:examId',
    element: ExamTakePage,
    requiresAuth: true,
    title: 'Take Exam - JEE AI Platform',
    description: 'Take your JEE practice exam',
  },
  {
    path: '/exams/:examId/results',
    element: ExamResultsPage,
    requiresAuth: true,
    title: 'Exam Results - JEE AI Platform',
    description: 'View your exam results and analysis',
  },
  {
    path: '/questions',
    element: QuestionBankPage,
    requiresAuth: true,
    title: 'Question Bank - JEE AI Platform',
    description: 'Browse practice questions',
  },
  {
    path: '/questions/:questionId',
    element: QuestionDetailPage,
    requiresAuth: true,
    title: 'Question Detail - JEE AI Platform',
  },
  {
    path: '/questions/create',
    element: CreateQuestionPage,
    requiresAuth: true,
    allowedRoles: ['admin', 'teacher'],
    title: 'Create Question - JEE AI Platform',
  },
  {
    path: '/profile',
    element: ProfilePage,
    requiresAuth: true,
    title: 'Profile - JEE AI Platform',
    description: 'Manage your profile and preferences',
  },
  {
    path: '/admin',
    element: AdminDashboard,
    requiresAuth: true,
    allowedRoles: ['admin'],
    title: 'Admin Dashboard - JEE AI Platform',
  },
  {
    path: '/admin/users',
    element: UserManagement,
    requiresAuth: true,
    allowedRoles: ['admin'],
    title: 'User Management - Admin',
  },
  {
    path: '/analytics',
    element: AnalyticsPage,
    requiresAuth: true,
    allowedRoles: ['admin', 'teacher'],
    title: 'Analytics - JEE AI Platform',
  },
  {
    path: '/settings',
    element: SettingsPage,
    requiresAuth: true,
    title: 'Settings - JEE AI Platform',
  },
  {
    path: '/help',
    element: HelpPage,
    requiresAuth: false,
    title: 'Help & Support - JEE AI Platform',
  },
];

// SEO component for dynamic meta tags
const SEOHelmet: React.FC<{ title: string; description?: string }> = ({
  title,
  description
}) => {
  React.useEffect(() => {
    document.title = title;

    if (description) {
      const metaDescription = document.querySelector('meta[name="description"]');
      if (metaDescription) {
        metaDescription.setAttribute('content', description);
      } else {
        const meta = document.createElement('meta');
        meta.name = 'description';
        meta.content = description;
        document.head.appendChild(meta);
      }
    }
  }, [title, description]);

  return null;
};

// Enhanced loading component with progress indicator
const EnhancedLoadingSpinner: React.FC = () => {
  const [progress, setProgress] = React.useState(0);

  React.useEffect(() => {
    const timer = setInterval(() => {
      setProgress((oldProgress) => {
        if (oldProgress === 100) {
          return 0;
        }
        const diff = Math.random() * 10;
        return Math.min(oldProgress + diff, 100);
      });
    }, 500);

    return () => {
      clearInterval(timer);
    };
  }, []);

  return (
    <div className="loading-container">
      <LoadingSpinner />
      <div className="loading-progress">
        <div className="progress-bar" style={{ width: `${progress}%` }} />
      </div>
      <p>Loading your content...</p>
    </div>
  );
};

// Main routing component
const AppRoutes: React.FC = () => {
  const isAuthenticated = useSelector((state: RootState) => state.auth.isAuthenticated);
  const user = useSelector((state: RootState) => state.auth.user);
  const location = useLocation();

  // Track routes for analytics
  useRouteTracking();

  // Check if user has required role for route
  const hasRequiredRole = (allowedRoles?: string[]): boolean => {
    if (!allowedRoles || allowedRoles.length === 0) return true;
    if (!user) return false;
    return allowedRoles.includes(user.role);
  };

  // Handle redirect after login
  const getRedirectPath = (): string => {
    const urlParams = new URLSearchParams(location.search);
    const redirectTo = urlParams.get('redirectTo');

    if (redirectTo && redirectTo.startsWith('/')) {
      return redirectTo;
    }

    // Default redirect based on user role
    if (user?.role === 'admin') {
      return '/admin';
    } else if (user?.role === 'teacher') {
      return '/analytics';
    } else {
      return '/dashboard';
    }
  };

  return (
    <ErrorBoundary>
      <Suspense fallback={<EnhancedLoadingSpinner />}>
        <Routes>
          {/* Public routes */}
          <Route
            path="/"
            element={
              isAuthenticated ? (
                <Navigate to={getRedirectPath()} replace />
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />

          {/* Generate routes from configuration */}
          {routeConfigs.map((config) => (
            <Route
              key={config.path}
              path={config.path}
              element={
                <>
                  <SEOHelmet title={config.title} description={config.description} />
                  {config.requiresAuth ? (
                    <ProtectedRoute
                      allowedRoles={config.allowedRoles}
                      redirectTo={`/login?redirectTo=${encodeURIComponent(location.pathname)}`}
                    >
                      <config.element />
                    </ProtectedRoute>
                  ) : (
                    // Redirect authenticated users away from login page
                    config.path === '/login' && isAuthenticated ? (
                      <Navigate to={getRedirectPath()} replace />
                    ) : (
                      <config.element />
                    )
                  )}
                </>
              }
            />
          ))}

          {/* Catch-all route for 404 */}
          <Route
            path="*"
            element={
              <>
                <SEOHelmet title="Page Not Found - JEE AI Platform" />
                <NotFoundPage />
              </>
            }
          />
        </Routes>
      </Suspense>
    </ErrorBoundary>
  );
};

export default AppRoutes;

// Export route utilities for use in other components
export { routeConfigs, useRouteTracking };

// Type definitions for route metadata
export interface RouteMetadata {
  title: string;
  description?: string;
  requiresAuth: boolean;
  allowedRoles?: string[];
}

// Hook for getting current route metadata
export const useCurrentRouteMetadata = (): RouteMetadata | null => {
  const location = useLocation();

  return React.useMemo(() => {
    const currentRoute = routeConfigs.find(
      route => route.path === location.pathname ||
      (route.path.includes(':') && matchPath(route.path, location.pathname))
    );

    return currentRoute ? {
      title: currentRoute.title,
      description: currentRoute.description,
      requiresAuth: currentRoute.requiresAuth,
      allowedRoles: currentRoute.allowedRoles,
    } : null;
  }, [location.pathname]);
};

// Utility function for path matching
const matchPath = (pattern: string, pathname: string): boolean => {
  const patternParts = pattern.split('/');
  const pathnameParts = pathname.split('/');

  if (patternParts.length !== pathnameParts.length) {
    return false;
  }

  return patternParts.every((part, index) => {
    if (part.startsWith(':')) {
      return true; // Parameter match
    }
    return part === pathnameParts[index];
  });
};

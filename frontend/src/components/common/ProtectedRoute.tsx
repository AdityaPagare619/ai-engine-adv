import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import { Alert, Result, Button } from 'antd';
import { ExclamationCircleOutlined, LockOutlined } from '@ant-design/icons';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: string[];
  requireVerification?: boolean;
  fallback?: React.ComponentType;
  redirectTo?: string;
  showAccessDenied?: boolean;
}

interface AccessDeniedProps {
  userRole: string;
  requiredRoles: string[];
  onRequestAccess?: () => void;
}

// Access denied component with actionable feedback
const AccessDenied: React.FC<AccessDeniedProps> = ({
  userRole,
  requiredRoles,
  onRequestAccess
}) => {
  const handleRequestAccess = () => {
    if (onRequestAccess) {
      onRequestAccess();
    } else {
      // Default action: mailto admin
      const subject = `Access Request for ${requiredRoles.join(', ')} Role`;
      const body = `Hi Admin,\n\nI am currently a ${userRole} and would like to request access to features requiring ${requiredRoles.join(' or ')} role.\n\nThank you.`;
      window.location.href = `mailto:admin@jeeai.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    }
  };

  const formatRoles = (roles: string[]): string => {
    if (roles.length === 1) return roles[0];
    if (roles.length === 2) return roles.join(' or ');
    return `${roles.slice(0, -1).join(', ')}, or ${roles[roles.length - 1]}`;
  };

  return (
    <div className="access-denied-container">
      <Result
        status="403"
        title="Access Denied"
        subTitle={
          <div>
            <p>
              You need to be a <strong>{formatRoles(requiredRoles)}</strong> to access this page.
            </p>
            <p>
              Your current role: <strong>{userRole}</strong>
            </p>
          </div>
        }
        icon={<LockOutlined />}
        extra={[
          <Button type="primary" key="request" onClick={handleRequestAccess}>
            Request Access
          </Button>,
          <Button key="back" onClick={() => window.history.back()}>
            Go Back
          </Button>,
        ]}
      />
    </div>
  );
};

// Account verification reminder component
const VerificationRequired: React.FC = () => {
  const user = useSelector((state: RootState) => state.auth.user);

  const handleResendVerification = async () => {
    try {
      // Implement resend verification logic
      const response = await fetch('/api/auth/resend-verification', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
      });

      if (response.ok) {
        Alert.success({
          message: 'Verification email sent successfully',
          description: 'Please check your email and click the verification link.',
        });
      }
    } catch (error) {
      Alert.error({
        message: 'Failed to send verification email',
        description: 'Please try again later or contact support.',
      });
    }
  };

  return (
    <div className="verification-required-container">
      <Result
        status="warning"
        title="Account Verification Required"
        subTitle={
          <div>
            <p>
              Please verify your email address (<strong>{user?.email}</strong>) to access this feature.
            </p>
            <p>
              Check your inbox for a verification email, or request a new one below.
            </p>
          </div>
        }
        icon={<ExclamationCircleOutlined />}
        extra={[
          <Button type="primary" key="resend" onClick={handleResendVerification}>
            Resend Verification Email
          </Button>,
          <Button key="logout" onClick={() => {
            // Implement logout logic
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            window.location.href = '/login';
          }}>
            Logout
          </Button>,
        ]}
      />
    </div>
  );
};

// Session expired component
const SessionExpired: React.FC = () => {
  const handleRelogin = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    window.location.href = '/login';
  };

  return (
    <div className="session-expired-container">
      <Result
        status="warning"
        title="Session Expired"
        subTitle="Your session has expired. Please log in again to continue."
        extra={[
          <Button type="primary" key="relogin" onClick={handleRelogin}>
            Log In Again
          </Button>,
        ]}
      />
    </div>
  );
};

// Main ProtectedRoute component
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  allowedRoles = [],
  requireVerification = false,
  fallback: FallbackComponent,
  redirectTo,
  showAccessDenied = true,
}) => {
  const location = useLocation();
  const authState = useSelector((state: RootState) => state.auth);
  const { isAuthenticated, user, sessionExpiry, isLoading } = authState;

  // Show loading state while authentication is being checked
  if (isLoading) {
    return (
      <div className="route-loading">
        <div className="loading-spinner">
          <div className="spinner" />
          <p>Checking authentication...</p>
        </div>
      </div>
    );
  }

  // Check if session has expired
  if (sessionExpiry && Date.now() > sessionExpiry) {
    return <SessionExpired />;
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated || !user) {
    const loginPath = redirectTo || `/login?redirectTo=${encodeURIComponent(location.pathname + location.search)}`;
    return <Navigate to={loginPath} state={{ from: location }} replace />;
  }

  // Check email verification if required
  if (requireVerification && !user.verified) {
    return <VerificationRequired />;
  }

  // Check role-based access
  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    if (FallbackComponent) {
      return <FallbackComponent />;
    }

    if (showAccessDenied) {
      return (
        <AccessDenied
          userRole={user.role}
          requiredRoles={allowedRoles}
          onRequestAccess={() => {
            // Custom access request logic can be implemented here
            console.log('Access requested for roles:', allowedRoles);
          }}
        />
      );
    }

    // Redirect to dashboard if access denied and not showing access denied page
    return <Navigate to="/dashboard" replace />;
  }

  // Check specific permissions if user has them
  const hasRequiredPermissions = (requiredPermissions: string[]): boolean => {
    if (!user.permissions || requiredPermissions.length === 0) return true;
    return requiredPermissions.every(permission => user.permissions.includes(permission));
  };

  // Log access for audit trail (in production, send to analytics service)
  React.useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      console.log('Route accessed:', {
        path: location.pathname,
        user: user.id,
        role: user.role,
        timestamp: new Date().toISOString(),
      });
    }
  }, [location.pathname, user.id, user.role]);

  // Auto-refresh token if needed (implement token refresh logic)
  React.useEffect(() => {
    const checkTokenExpiry = () => {
      if (sessionExpiry) {
        const timeUntilExpiry = sessionExpiry - Date.now();
        const warningTime = 5 * 60 * 1000; // 5 minutes

        if (timeUntilExpiry <= warningTime && timeUntilExpiry > 0) {
          // Show session warning
          Alert.warning({
            message: 'Session Expiring Soon',
            description: 'Your session will expire in 5 minutes. Please save your work.',
            duration: 10,
          });
        }
      }
    };

    const interval = setInterval(checkTokenExpiry, 60000); // Check every minute
    return () => clearInterval(interval);
  }, [sessionExpiry]);

  // All checks passed, render children
  return <>{children}</>;
};

export default ProtectedRoute;

// Higher-order component for role-based rendering
export const withRoleGuard = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  allowedRoles: string[]
) => {
  const RoleGuardedComponent: React.FC<P> = (props) => {
    return (
      <ProtectedRoute allowedRoles={allowedRoles}>
        <WrappedComponent {...props} />
      </ProtectedRoute>
    );
  };

  RoleGuardedComponent.displayName = `withRoleGuard(${WrappedComponent.displayName || WrappedComponent.name})`;
  return RoleGuardedComponent;
};

// Hook for checking user permissions in components
export const usePermissions = () => {
  const user = useSelector((state: RootState) => state.auth.user);

  const hasRole = (role: string): boolean => {
    return user?.role === role;
  };

  const hasAnyRole = (roles: string[]): boolean => {
    return user ? roles.includes(user.role) : false;
  };

  const hasPermission = (permission: string): boolean => {
    return user?.permissions?.includes(permission) ?? false;
  };

  const hasAnyPermission = (permissions: string[]): boolean => {
    return user?.permissions ? permissions.some(p => user.permissions!.includes(p)) : false;
  };

  const hasAllPermissions = (permissions: string[]): boolean => {
    return user?.permissions ? permissions.every(p => user.permissions!.includes(p)) : false;
  };

  return {
    user,
    hasRole,
    hasAnyRole,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    isAdmin: hasRole('admin'),
    isTeacher: hasRole('teacher'),
    isStudent: hasRole('student'),
  };
};

// Component for conditional rendering based on roles/permissions
export const ConditionalRender: React.FC<{
  allowedRoles?: string[];
  requiredPermissions?: string[];
  fallback?: React.ReactNode;
  children: React.ReactNode;
}> = ({ allowedRoles = [], requiredPermissions = [], fallback = null, children }) => {
  const { hasAnyRole, hasAllPermissions } = usePermissions();

  const hasRoleAccess = allowedRoles.length === 0 || hasAnyRole(allowedRoles);
  const hasPermissionAccess = requiredPermissions.length === 0 || hasAllPermissions(requiredPermissions);

  if (hasRoleAccess && hasPermissionAccess) {
    return <>{children}</>;
  }

  return <>{fallback}</>;
};

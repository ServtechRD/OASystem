import React from 'react';
import { BrowserRouter, Route, Switch, Redirect } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import EmployeeManagement from './components/EmployeeManagement';
import { AuthProvider, useAuth } from './contexts/AuthContext';

const theme = createTheme();

// Protected Route Component
const PrivateRoute = ({ children, ...rest }) => {
  const { isAuthenticated } = useAuth();
  return (
    <Route
      {...rest}
      render={({ location }) =>
        isAuthenticated ? (
          children
        ) : (
          <Redirect to={{ pathname: "/login", state: { from: location } }} />
        )
      }
    />
  );
};

const App = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <BrowserRouter>
          <Switch>
            <Route exact path="/login" component={Login} />
            <PrivateRoute path="/">
              <Dashboard />
            </PrivateRoute>
          </Switch>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;

import React from 'react';
import { Box, Button, Paper, Stack, Typography } from '@mui/material';

export default class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: '' };
  }

  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      message: error?.message || 'Unknown application error.',
    };
  }

  componentDidCatch(error, info) {
    console.error('AppErrorBoundary caught error:', error, info);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <Box sx={{ p: 4 }}>
          <Paper elevation={2} sx={{ p: 4, borderRadius: 3, maxWidth: 760, mx: 'auto' }}>
            <Stack spacing={2}>
              <Typography variant="h4" fontWeight={700}>
                Crown dashboard error
              </Typography>
              <Typography variant="body1">
                The dashboard hit a runtime error and could not continue safely.
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {this.state.message}
              </Typography>
              <Box>
                <Button variant="contained" onClick={this.handleReload}>
                  Reload Application
                </Button>
              </Box>
            </Stack>
          </Paper>
        </Box>
      );
    }

    return this.props.children;
  }
}

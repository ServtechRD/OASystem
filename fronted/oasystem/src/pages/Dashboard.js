import React from 'react';
import { Box } from '@mui/material';
import Sidebar from '../components/Sidebar';
import AttendanceSystem from '../components/AttendanceSystem';
import EmployeeManagement from '../components/EmployeeManagement';
import LeaveRecords from '../components/LeaveRecords';


import { Switch, Route } from 'react-router-dom';


const Dashboard = () => {
  return (
    <Box sx={{ display: 'flex' }}>

      <Sidebar />
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Switch>
          <Route exact path="/" component={AttendanceSystem} />
          <Route path="/employees" component={EmployeeManagement} />
          <Route path="/leave-records" component={LeaveRecords} />
        </Switch>
      </Box>

    </Box>
  );
};

export default Dashboard;

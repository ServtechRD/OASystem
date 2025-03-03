import React from "react";
import { Box, Button } from "@mui/material";
import LogoutIcon from "@mui/icons-material/Logout";
import Sidebar from "../components/Sidebar";
import AttendanceSystem from "../components/AttendanceSystem";
import EmployeeManagement from "../components/EmployeeManagement";
import LeaveRecords from "../components/LeaveRecords";

import { Switch, Route, useHistory } from "react-router-dom";

const Dashboard = () => {
  const history = useHistory();

  const handleLogout = () => {
    // 您可以在这里添加任何登出逻辑，例如清除本地存储的令牌
    localStorage.removeItem("authToken"); // 假设您使用authToken存储认证信息

    // 重定向到登录页面
    history.push("/login");
  };

  return (
    <Box sx={{ display: "flex" }}>
      <Sidebar />

      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        {/* 添加登出按钮在右上角 */}
        <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 2 }}>
          <Button
            variant="contained"
            color="error"
            startIcon={<LogoutIcon />}
            onClick={handleLogout}
          >
            登出
          </Button>
        </Box>

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

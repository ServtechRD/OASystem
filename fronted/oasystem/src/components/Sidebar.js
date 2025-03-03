import React from "react";
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Box,
  Divider,
} from "@mui/material";

import { Link, useHistory } from "react-router-dom";

import AccessTimeIcon from "@mui/icons-material/AccessTime";

import PeopleIcon from "@mui/icons-material/People";
import FormatListBulletedIcon from "@mui/icons-material/FormatListBulleted";
import LogoutIcon from "@mui/icons-material/Logout";

const drawerWidth = 240;

const Sidebar = () => {
  const history = useHistory();

  const handleLogout = () => {
    // 清除認證信息
    localStorage.removeItem("authToken");

    // 導向登入頁面
    history.push("/login");
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: drawerWidth,
          boxSizing: "border-box",
        },
      }}
    >
      <Box sx={{ overflow: "auto", mt: 8 }}>
        <List>
          <ListItem button component={Link} to="/employees">
            <ListItemIcon>
              <PeopleIcon />
            </ListItemIcon>
            <ListItemText primary="員工管理" />
          </ListItem>
          <ListItem button component={Link} to="/">
            <ListItemIcon>
              <AccessTimeIcon />
            </ListItemIcon>
            <ListItemText primary="差勤系統" />
          </ListItem>
        </List>

        <ListItem button component={Link} to="/leave-records">
          <ListItemIcon>
            <FormatListBulletedIcon />
          </ListItemIcon>
          <ListItemText primary="請假記錄" />
        </ListItem>
        {/* 添加分隔線 */}
        <Divider sx={{ mt: 2, mb: 2 }} />

        {/* 登出按鈕 */}
        <ListItem button onClick={handleLogout}>
          <ListItemIcon>
            <LogoutIcon color="error" />
          </ListItemIcon>
          <ListItemText primary="登出" sx={{ color: "error.main" }} />
        </ListItem>
      </Box>
    </Drawer>
  );
};

export default Sidebar;

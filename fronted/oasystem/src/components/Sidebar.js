import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Box
} from '@mui/material';

import { Link } from 'react-router-dom';

import AccessTimeIcon from '@mui/icons-material/AccessTime';

import PeopleIcon from '@mui/icons-material/People';
import FormatListBulletedIcon from '@mui/icons-material/FormatListBulleted';


const drawerWidth = 240;

const Sidebar = () => {
  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <Box sx={{ overflow: 'auto', mt: 8 }}>
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

      </Box>
    </Drawer>
  );
};

export default Sidebar;

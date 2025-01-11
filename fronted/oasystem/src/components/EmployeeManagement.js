import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Button, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions,
  TextField,
  IconButton,
  Typography,

  Snackbar,
  Alert // 新增 Alert 組件


} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import axios from 'axios';
import {employeeAPI} from '../services/api';

const EmployeeManagement = () => {
   // 新增 snackbar 相關的 state
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success' // 'success' | 'error' | 'info' | 'warning'
  }); 




  const [employees, setEmployees] = useState([]);
  const [open, setOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [formData, setFormData] = useState({
    emp_id: '',
    name: '',
    email: '',
    description:'',
    phone:'',
    position:'',
    specialty:'',

    work_start_time: '09:00',
    work_end_time: '18:30',
    annual_leave_days: 1,
    sick_leave_days:14,

    login_account: '',
    login_password: '' // 新增密碼欄位
  });

  // 列定義
  const columns = [
    { field: 'emp_id', headerName: '員工編號', width: 130 },
    { field: 'name', headerName: '姓名', width: 130 },
    { field: 'login_account', headerName: '登入帳號', width: 200 },
    { field: 'work_start_time', headerName: '上班時間', width: 130 },
    { field: 'work_end_time', headerName: '下班時間', width: 130 },
    { field: 'annual_leave_days', headerName: '特休天數', width: 130 },
    { field: 'sick_leave_days', headerName: '病假天數', width: 130 },


    {
      field: 'actions',
      headerName: '操作',
      width: 130,
      sortable: false,
      renderCell: (params) => (
        <Box>
          <IconButton 
            color="primary" 
            onClick={() => handleEdit(params.row)}
          >
            <EditIcon />
          </IconButton>
          <IconButton 
            color="error" 
            onClick={() => handleDelete(params.row.id)}
          >
            <DeleteIcon />
          </IconButton>
        </Box>
      )
    }
  ];

  // 載入員工資料
  const fetchEmployees = async () => {
    try {
      setLoading(true);
      const response = await employeeAPI.getAllEmployees(); //axios.get('http://192.168.1.234:39200/base/employees');
      setEmployees(response.data);
    } catch (error) {
      console.error('Error fetching employees:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees();
  }, []);




   // 新增關閉 snackbar 的處理函數
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };


  // 處理新增/編輯表單提交
  const handleSubmit = async () => {
    try {
      if (editMode) {
        //await axios.put(`http://192.168.1.234:39200/base/employees/${selectedEmployee.id}`, formData);
        formData['email'] = formData['login_account'];
        formData['login_password'] = selectedEmployee.login_password;
        await employeeAPI.updateEmployee(selectedEmployee.id,formData);
         setSnackbar({
          open: true,
          message: '員工資料更新成功！',
          severity: 'success'
        });


      } else {
        formData['email'] = formData['login_account']; 
        //await axios.post('http://192.168.1.234:39200/base/employees', formData);
        await employeeAPI.createEmployee(formData);
        
        setSnackbar({
          open: true,
          message: '新增員工成功！',
          severity: 'success'
        });


      }
      fetchEmployees();
      handleClose();
    } catch (error) {
      console.error('Error saving employee:', error);
       setSnackbar({
        open: true,
        message: `操作失敗：${error.message}`,
        severity: 'error'
      });


    }
  };

  // 處理刪除
  const handleDelete = async (id) => {
    if (window.confirm('確定要刪除這筆資料嗎？')) {
      try {
        //await axios.delete(`http://192.168.1.234:39200/base/employees/${id}`);
        await employeeAPI.deleteEmployee(id);
         setSnackbar({
          open: true,
          message: '員工資料已刪除',
          severity: 'success'
        });


        fetchEmployees();
      } catch (error) {
        console.error('Error deleting employee:', error);
         setSnackbar({
          open: true,
          message: `刪除失敗：${error.message}`,
          severity: 'error'
        });
      }
    }
  };

  // 處理編輯
  const handleEdit = (employee) => {
    setSelectedEmployee(employee);
    setFormData({
      emp_id: employee.emp_id,
      name: employee.name,
      email: employee.email,
      description: employee.description,
      specialty:employee.specialty,
      phone:employee.phone,
      position:employee.position,
      login_account: employee.login_account,
      login_password: employee.login_password
    });
    setEditMode(true);
    setOpen(true);
  };

  // 處理新增
  const handleAdd = () => {
    setSelectedEmployee(null);
    setFormData({
      emp_id: '',
      name: '',
      email: '',
      description:'',
      phone:'',
      specialty:'',
      position:'',
      login_account: '',
      login_password: ''
    });
    setEditMode(false);
    setOpen(true);
  };

  // 關閉對話框
  const handleClose = () => {
    setOpen(false);
    setEditMode(false);
    setSelectedEmployee(null);
    setFormData({
      emp_id: '',
      name: '',
      login_account: '',
      login_password:'',
      descrription:'',
      position:'',
      specialty:'',
      phone:''
    });
  };

  return (
    <Box sx={{ height: 'calc(100vh - 100px)', width: '100%', p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h5">員工基本資料管理</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAdd}
        >
          新增員工
        </Button>
      </Box>

      <DataGrid
        rows={employees}
        columns={columns}
        pageSize={10}
        rowsPerPageOptions={[10]}
        disableSelectionOnClick
        loading={loading}
        autoHeight
      />

      {/* 新增/編輯對話框 */}
      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>{editMode ? '編輯員工資料' : '新增員工'}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="員工編號"
            fullWidth
            value={formData.emp_id}
            onChange={(e) => setFormData({ ...formData, emp_id: e.target.value })}
          />
          <TextField
            margin="dense"
            label="姓名"
            fullWidth
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />
          <TextField
            margin="dense"
            label="登入帳號"
            fullWidth
            value={formData.login_account}
            onChange={(e) => setFormData({ ...formData, login_account: e.target.value })}
          />

          {!editMode && ( // 只在新增時顯示密碼欄位
          <TextField
            margin="dense"
            label="登入密碼"
            type="password"
            fullWidth
            value={formData.login_password}
            onChange={(e) => setFormData({ ...formData, login_password: e.target.value })}
          />
           )}

            <TextField
          margin="dense"
          label="上班時間"
          type="time"
          fullWidth
          value={formData.work_start_time}
          onChange={(e) => setFormData({ ...formData, work_start_time: e.target.value })}
          InputLabelProps={{ shrink: true }}
          inputProps={{ step: 300 }}
        />
        <TextField
          margin="dense"
          label="下班時間"
          type="time"
          fullWidth
          value={formData.work_end_time}
          onChange={(e) => setFormData({ ...formData, work_end_time: e.target.value })}
          InputLabelProps={{ shrink: true }}
          inputProps={{ step: 300 }}
        />
        <TextField
          margin="dense"
          label="年度特休天數"
          type="number"
          fullWidth
          value={formData.annual_leave_days}
          onChange={(e) => setFormData({ ...formData, annual_leave_days: Number(e.target.value) })}
          InputProps={{ inputProps: { min: 0 } }}
        />
        <TextField
          margin="dense"
          label="年度病假天數"
          type="number"
          fullWidth
          value={formData.sick_leave_days}
          onChange={(e) => setFormData({ ...formData, sick_leave_days: Number(e.target.value) })}
          InputProps={{ inputProps: { min: 0 } }}
        />


        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>取消</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editMode ? '更新' : '新增'}
          </Button>
        </DialogActions>
      </Dialog>

       {/* 新增 Snackbar 組件 */}
      <Snackbar 
        open={snackbar.open} 
        autoHideDuration={3000} 
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleCloseSnackbar} 
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>


    </Box>
  );
};

export default EmployeeManagement;

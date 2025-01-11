import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Paper, 
  Typography,
  TextField,
  Grid,
  Autocomplete,
  Snackbar,
  Alert,
  Button  // 新增 Button
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { leaveAPI } from '../services/api';
import SearchIcon from '@mui/icons-material/Search';  // 新增搜尋圖標

import DownloadIcon from '@mui/icons-material/Download'; // 新增下載圖標



import dayjs from 'dayjs';
import 'dayjs/locale/zh-tw';

// 設置 dayjs 語系
dayjs.locale('zh-tw');

const LeaveRecords = () => {
  // 獲取當月第一天和最後一天
  const getMonthRange = () => {
    const now = dayjs();
    return {
      startDate: now.startOf('month').format('YYYY-MM-DD 00:00:00'),
      endDate: now.endOf('month').format('YYYY-MM-DD 23:59:59')
    };
  };

  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [dateRange, setDateRange] = useState(getMonthRange());
  const [error, setError] = useState(null);

  // 新增員工清單 state
  const [employees, setEmployees] = useState([]);


 // 為 Autocomplete 添加「全部員工」選項
  const employeeOptions = [
    { emp_id: '', name: '全部員工' }, // 添加全部員工選項
    ...employees
  ];


  
  // 預設過濾掉 draft 狀態
  const [filterModel, setFilterModel] = useState({
    items: [
      {
        field: 'status',
        operator: 'notEquals',
        value: '草稿'
      }
    ]
  });

  const columns = [
    { field: 'emp_id', headerName: '員工編號', width: 130 },
     { 
      field: 'emp_name', 
      headerName: '員工姓名', 
      width: 130,
      valueGetter: (params) => {
        const employee = employees.find(emp => emp.emp_id === params.row.emp_id);
        return employee?.name || '';
      }
    },
    { field: 'leave_type', headerName: '假別', width: 130 },
    { 
      field: 'start_datetime', 
      headerName: '開始時間', 
      width: 200,
      valueFormatter: (params) => {
        return dayjs(params.value).format('YYYY-MM-DD HH:mm');
      }

    },
    { 
      field: 'end_datetime', 
      headerName: '結束時間', 
      width: 200,
      valueFormatter: (params) => {
        return dayjs(params.value).format('YYYY-MM-DD HH:mm');
      }
    },
    { 
      field: 'status', 
      headerName: '狀態', 
      width: 130,
      valueFormatter: (params) => {
        const statusMap = {
          draft: '草稿',
          pending: '待審核',
          approved: '已核准',
          rejected: '已拒絕'
        };
        return statusMap[params.value] || params.value;
      }
    },
    { field: 'note', headerName: '備註', width: 200 },
  ];

  const fetchLeaveRecords = async () => {
    try {
      setLoading(true);
      setError(null);
      let response;
      
      if (selectedEmployee) {
        response = await leaveAPI.getEmployeeLeaveRecords(
          selectedEmployee.emp_id,
          dateRange.startDate,
          dateRange.endDate
        );
      } else {
        response = await leaveAPI.getLeaveRecords(
          dateRange.startDate,
          dateRange.endDate
        );
      }
      
      setRecords(response.data);
    } catch (error) {
      console.error('Error fetching leave records:', error);
      setError('載入請假記錄失敗');
    } finally {
      setLoading(false);
    }
  };

  // 獲取員工清單
  const fetchEmployees = async () => {
    try {
      const response = await leaveAPI.getAllEmployees();
      setEmployees(response.data);
    } catch (error) {
      console.error('Error fetching employees:', error);
      setError('載入員工資料失敗');
    }
  };

  // 在組件掛載時獲取員工清單
  useEffect(() => {
    fetchEmployees();
  }, []);




  // 修改查詢函數，改為手動觸發
  const handleSearch = async () => {
    try {
      setLoading(true);
      setError(null);
      setRecords([]);

      let response;
      
      if (selectedEmployee?.emp_id) {
        response = await leaveAPI.getEmployeeLeaveRecords(
          selectedEmployee.emp_id,
          dateRange.startDate,
          dateRange.endDate
        );
      } else {
        response = await leaveAPI.getLeaveRecords(
          dateRange.startDate,
          dateRange.endDate
        );
      }
      
      setRecords(response.data);
    } catch (error) {
      console.error('Error fetching leave records:', error);
      setError('查無資料');
      setRecords([]);
    } finally {
      setLoading(false);
    }
  };

  
 // 新增下載 CSV 的函數
  const handleDownloadCSV = () => {
    if (records.length === 0) return;

    // 準備 CSV 內容
    const headers = [
      '員工編號',
      '員工姓名',
      '假別',
      '開始時間',
      '結束時間',
      '狀態',
      '備註'
    ];

    const csvData = records.map(record => {
      const employee = employees.find(emp => emp.emp_id === record.emp_id);
      const statusMap = {
        draft: '草稿',
        pending: '待審核',
        approved: '已核准',
        rejected: '已拒絕'
      };

      return [
        record.emp_id,
        employee?.name || '',
        record.leave_type,
        dayjs(record.start_datetime).format('YYYY-MM-DD HH:mm'),
        dayjs(record.end_datetime).format('YYYY-MM-DD HH:mm'),
        statusMap[record.status] || record.status,
        record.note
      ];
    });

    // 組合 CSV 內容
    const csvContent = [
      headers.join(','),
      ...csvData.map(row => row.map(cell => 
        // 處理包含逗號、換行或引號的內容
        `"${String(cell).replace(/"/g, '""')}"`
      ).join(','))
    ].join('\n');

    // 創建並下載檔案
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `請假記錄_${dayjs().format('YYYYMMDD_HHmmss')}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };  





  const handleDateChange = (field) => (event) => {
    const date = dayjs(event.target.value);
    setDateRange(prev => ({
      ...prev,
      [field]: field === 'startDate' 
        ? date.format('YYYY-MM-DD 00:00:00')
        : date.format('YYYY-MM-DD 23:59:59')
    }));
  };

  const handleEmployeeSearch = async (event, newValue) => {
    if (newValue) {
      try {
        const response = await leaveAPI.getEmployeeByEmpId(newValue.emp_id);
        setSelectedEmployee(response.data);
      } catch (error) {
        console.error('Error fetching employee:', error);
        setError('查詢員工資料失敗');
      }
    } else {
      setSelectedEmployee(null);
    }
  };

  return (
    <Box sx={{ height: 'calc(100vh - 100px)', width: '100%', p: 2 }}>
      <Typography variant="h5" gutterBottom>
        請假記錄查詢
      </Typography>
      
        {/* 修改查詢條件布局 */}
      <Box sx={{ 
        display: 'flex', 
        gap: 2, 
        mb: 2,
        alignItems: 'center'
      }}>

          <TextField
            label="開始日期"
            type="date"
            value={dateRange.startDate.split(' ')[0]}
            onChange={handleDateChange('startDate')}
            fullWidth
            InputLabelProps={{
              shrink: true,
            }}
               sx={{ width: 200 }}
          />
          <TextField
            label="結束日期"
            type="date"
            value={dateRange.endDate.split(' ')[0]}
            onChange={handleDateChange('endDate')}
            fullWidth
            InputLabelProps={{
              shrink: true,
            }}
             sx={{ width: 200 }}
          />
      <Autocomplete
        options={employeeOptions}
        getOptionLabel={(option) => 
          option.emp_id ? `${option.emp_id} - ${option.name}` : option.name
        }
        value={selectedEmployee || employeeOptions[0]} // 預設選擇「全部員工」
        onChange={(event, newValue) => {
          // 如果選擇「全部員工」或清空選擇，則設為 null
          setSelectedEmployee(newValue?.emp_id ? newValue : null);
        }}
        renderInput={(params) => (
          <TextField
            {...params}
            label="員工查詢"
            fullWidth
          />
        )}
        isOptionEqualToValue={(option, value) => 
          option.emp_id === value?.emp_id
        }
         sx={{ width: 300 }}

      />

          <Button
            variant="contained"
            startIcon={<SearchIcon />}
            onClick={handleSearch}
            sx={{ height: '40px' }}  // 使按鈕高度與其他輸入框一致
          >
            查詢
          </Button>
     </Box>


      <Paper sx={{ height: '100%', width: '100%' }}>

 <Box sx={{ 
        p: 2, 
        display: 'flex', 
        justifyContent: 'flex-end',
        borderBottom: '1px solid rgba(224, 224, 224, 1)'
      }}>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={handleDownloadCSV}
          disabled={records.length === 0}
        >
          下載 CSV
        </Button>
      </Box>




        <DataGrid
          rows={records}
          columns={columns}
          pageSize={10}
          rowsPerPageOptions={[10, 25, 50]}
          loading={loading}
          disableSelectionOnClick
          autoHeight
          filterModel={filterModel}
          onFilterModelChange={(model) => setFilterModel(model)}
          components={{
            NoRowsOverlay: () => (
              <Box sx={{ 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center',
                height: '100%'
              }}>
                {loading ? '載入中...' : '無資料'}
              </Box>
            )
          }}
        />
      </Paper>

      <Snackbar 
        open={!!error} 
        autoHideDuration={3000} 
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default LeaveRecords;

import React, { useState, useEffect, useRef } from "react";
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider,
  CircularProgress,
} from "@mui/material";
import { useAuth } from "../contexts/AuthContext";
import { createWebSocket } from "../services/api";
import { leaveAPI } from "../services/api";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const AttendanceSystem = () => {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);

  // 新增請假記錄狀態
  const [leaveRecords, setLeaveRecords] = useState([]);
  // 新增請假統計狀態
  const [leaveStats, setLeaveStats] = useState({
    annual: { used: 0, total: 0 },
    sick: { used: 0, total: 0 },
    other: { used: 0 },
  });

  // 獲取當年度的開始和結束時間
  const getYearRange = () => {
    const now = new Date();
    const year = now.getFullYear();
    return {
      startDate: `${year}-01-01 00:00:00`,
      endDate: `${year}-12-31 23:59:59`,
    };
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    wsRef.current = createWebSocket("/ws/leave"); //new WebSocket('ws://192.168.1.234:39200/ws/leave');

    // 添加onopen事件处理器，等待连接成功
    wsRef.current.onopen = () => {
      console.log("WebSocket连接已建立");
      // 连接成功后再调用handleSendStart
      handleSendStart();
    };

    wsRef.current.onmessage = (event) => {
      console.log(event);

      // 直接使用 event.data，因為它已經是文字字串
      setMessages((prev) => [
        ...prev,
        {
          content: event.data,
          isUser: false, // 標記為系統回覆訊息
        },
      ]);

      setIsLoading(false);
      scrollToBottom();
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 計算請假天數（假設一天工作 8 小時）
  const calculateLeaveDays = (startTime, endTime) => {
    const start = new Date(startTime);
    const end = new Date(endTime);
    const hours = (end - start) / (1000 * 60 * 60);
    return hours / 8;
  };

  // 統計請假記錄
  const calculateLeaveStats = (records) => {
    const stats = {
      annual: { used: 0, total: user?.annual || 0 },
      sick: { used: 0, total: user?.sick || 0 },
      other: { used: 0 },
    };

    records.forEach((record) => {
      // 只統計已申請和已核准的請假
      if (!["requested", "approved"].includes(record.status)) return;

      const days = calculateLeaveDays(
        record.start_datetime,
        record.end_datetime
      );

      switch (record.leave_type) {
        case "特休":
          stats.annual.used += days;
          break;
        case "病假":
          stats.sick.used += days;
          break;
        default:
          stats.other.used += days;
      }
    });

    return stats;
  };

  // 載入請假記錄
  const fetchLeaveRecords = async () => {
    try {
      const { startDate, endDate } = getYearRange();
      const response = await leaveAPI.getEmployeeLeaveRecords(
        user.emp_id,
        startDate,
        endDate
      );
      setLeaveRecords(response.data);
      const stats = calculateLeaveStats(response.data);
      setLeaveStats(stats);
    } catch (error) {
      console.error("Error fetching leave records:", error);
    }
  };

  useEffect(() => {
    if (user?.emp_id) {
      fetchLeaveRecords();
    }
  }, [user]);

  // 只定義表格相關的 Markdown 組件
  const MarkdownComponents = {
    table: ({ children }) => (
      <TableContainer component={Paper} sx={{ my: 1 }}>
        <Table size="small">{children}</Table>
      </TableContainer>
    ),
    thead: ({ children }) => <TableHead>{children}</TableHead>,
    tbody: ({ children }) => <TableBody>{children}</TableBody>,
    tr: ({ children }) => <TableRow>{children}</TableRow>,
    td: ({ children }) => <TableCell>{children}</TableCell>,
    th: ({ children }) => (
      <TableCell sx={{ fontWeight: "bold" }}>{children}</TableCell>
    ),
  };

  const handleSendStart = () => {
    if (wsRef.current) {
      wsRef.current.send(
        JSON.stringify({
          message: "***" + "@@" + user.emp_id + "@@",
          userId: user.id,
        })
      );
    }
  };

  const handleSendMessage = () => {
    if (wsRef.current && newMessage.trim()) {
      wsRef.current.send(
        JSON.stringify({
          message: newMessage + "@@" + user.emp_id + "@@",
          userId: user.id,
        })
      );

      // Add user's message to the messages array
      setMessages((prev) => [
        ...prev,
        {
          content: newMessage,
          isUser: true, // Flag to identify user's messages
        },
      ]);

      setNewMessage("");
      setIsLoading(true);
    }
  };

  return (
    <Box sx={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <TableContainer component={Paper} sx={{ mb: 2 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>姓名</TableCell>
              <TableCell>工號</TableCell>
              <TableCell>特休(已請/可請)</TableCell>
              <TableCell>病假(已請/可請)</TableCell>
              <TableCell>其它假</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <TableRow>
              <TableCell>{user?.emp_name}</TableCell>
              <TableCell>{user?.emp_id}</TableCell>
              <TableCell>
                {leaveStats.annual.used.toFixed(1)}/{leaveStats.annual.total}
              </TableCell>
              <TableCell>
                {leaveStats.sick.used.toFixed(1)}/{leaveStats.sick.total}
              </TableCell>
              <TableCell>{leaveStats.other.used.toFixed(1)}</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>

      <Paper
        sx={{
          flex: 1,
          mb: 2,
          p: 2,
          overflow: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 1,
        }}
      >
        {messages.map((msg, index) => (
          <Box
            key={index}
            sx={{
              alignSelf: msg.isUser ? "flex-end" : "flex-start",
              maxWidth: "70%",
              bgcolor: msg.isUser ? "primary.light" : "grey.100",
              p: 1,
              borderRadius: 2,
              color: msg.isUser ? "white" : "text.primary",
            }}
          >
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={MarkdownComponents}
            >
              {msg.content}
            </ReactMarkdown>
          </Box>
        ))}
        {isLoading && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              p: 2,
            }}
          >
            <CircularProgress size={24} />
            <Typography variant="body2" sx={{ ml: 1 }}>
              載入中...
            </Typography>
          </Box>
        )}
        <div ref={messagesEndRef} />
      </Paper>

      <Box sx={{ display: "flex", gap: 1 }}>
        <TextField
          fullWidth
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="輸入訊息..."
          onKeyPress={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSendMessage();
            }
          }}
        />
        <Button
          variant="contained"
          onClick={handleSendMessage}
          disabled={isLoading}
        >
          發送
        </Button>
      </Box>
    </Box>
  );
};

export default AttendanceSystem;

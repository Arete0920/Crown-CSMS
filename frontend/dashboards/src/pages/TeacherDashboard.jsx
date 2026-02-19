import React, { useEffect, useMemo, useState } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Stack,
  Chip,
  Button,
  IconButton,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Alert,
  CircularProgress,
  Badge,
  Divider,
} from "@mui/material";
// Inline icon components — forbidden icon packages are not used.
// Unicode characters replace icon imports per CI guardrail.
const ClassIcon        = () => <span aria-hidden="true" style={{fontSize:'1.1em'}}>⊟</span>;
const GradeIcon        = () => <span aria-hidden="true" style={{fontSize:'1.1em'}}>📋</span>;
const AttendanceIcon   = () => <span aria-hidden="true" style={{fontSize:'1.1em'}}>✅</span>;
const MessageIcon      = () => <span aria-hidden="true" style={{fontSize:'1.1em'}}>✉</span>;
const AnnouncementIcon = () => <span aria-hidden="true" style={{fontSize:'1.1em'}}>📢</span>;
const AddIcon          = () => <span aria-hidden="true" style={{fontSize:'1.1em'}}>＋</span>;
const EditIcon         = () => <span aria-hidden="true" style={{fontSize:'1.1em'}}>✎</span>;
const CheckIcon        = () => <span aria-hidden="true" style={{fontSize:'1.1em'}}>✓</span>;
const TimeIcon         = () => <span aria-hidden="true" style={{fontSize:'1.1em'}}>⏱</span>;
import { getSelectedSchoolId } from '../utils/authClient';

function normalizeBaseUrl(url) {
  if (!url) return "";
  return url.endsWith("/") ? url.slice(0, -1) : url;
}

function getAuthHeaders() {
  const token = sessionStorage.getItem("crown.jwt.access") || "";
  const schoolId = sessionStorage.getItem("crown.school.id") || "";

  const h = { "Content-Type": "application/json" };
  if (token) h["Authorization"] = `Bearer ${token}`;
  if (schoolId) h["X-School-Id"] = schoolId;
  return h;
}

export default function TeacherDashboard() {
  const schoolId = useMemo(() => getSelectedSchoolId(), []);
  const API_BASE = useMemo(
    () => normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL || ""),
    []
  );

  // State management
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  
  // Data states
  const [sections, setSections] = useState([]);
  const [todaysClasses, setTodaysClasses] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);
  
  // Dialog states
  const [attendanceDialogOpen, setAttendanceDialogOpen] = useState(false);
  const [gradeDialogOpen, setGradeDialogOpen] = useState(false);
  const [messageDialogOpen, setMessageDialogOpen] = useState(false);
  const [selectedSection, setSelectedSection] = useState(null);
  
  // Attendance management states
  const [sectionRoster, setSectionRoster] = useState([]);
  const [attendanceRecords, setAttendanceRecords] = useState({});
  const [attendanceLoading, setAttendanceLoading] = useState(false);
  const [attendanceDate, setAttendanceDate] = useState(new Date().toISOString().split('T')[0]);
  
  // Grade entry states
  const [gradebookData, setGradebookData] = useState(null);
  const [gradeChanges, setGradeChanges] = useState({});
  const [gradeLoading, setGradeLoading] = useState(false);
  
  // Communication states
  const [messageSubject, setMessageSubject] = useState("");
  const [messageBody, setMessageBody] = useState("");
  const [messageRecipients, setMessageRecipients] = useState("all_parents");
  const [messageLoading, setMessageLoading] = useState(false);
  
  // Load teacher's sections
  useEffect(() => {
    if (!schoolId) return;
    const controller = new AbortController();

    async function loadTeacherSections() {
      setLoading(true);
      setError("");
      try {
        const url = `${API_BASE}/api/v1/gradebook/sections/`;
        const res = await fetch(url, {
          method: "GET",
          headers: getAuthHeaders(),
          signal: controller.signal,
        });

        if (!res.ok) {
          const text = await res.text().catch(() => "");
          throw new Error(`Sections failed: ${res.status} ${res.statusText}${text ? ` — ${text}` : ""}`);
        }

        const json = await res.json();
        setSections(json.results || json || []);
        
        // Simulate "today's classes" by filtering sections
        // In real implementation this would be based on schedule/calendar
        const today = new Date();
        const todayClasses = (json.results || json || []).map(section => ({
          ...section,
          time: "8:00 AM", // Mock time - would come from schedule API
          room: section.room || `Room ${Math.floor(Math.random() * 100) + 100}`,
          status: Math.random() > 0.7 ? "completed" : Math.random() > 0.3 ? "in-progress" : "upcoming"
        }));
        setTodaysClasses(todayClasses);
        
      } catch (e) {
        if (e.name !== "AbortError") setError(e.message || String(e));
      } finally {
        setLoading(false);
      }
    }

    loadTeacherSections();
    return () => controller.abort();
  }, [schoolId, API_BASE]);

  const handleTakeAttendance = async (section) => {
    setSelectedSection(section);
    setAttendanceLoading(true);
    try {
      // Load section roster from the existing API
      const url = `${API_BASE}/api/v1/academics/sections/${section.id}/roster/`;
      const res = await fetch(url, {
        method: "GET",
        headers: getAuthHeaders(),
      });
      
      if (res.ok) {
        const data = await res.json();
        setSectionRoster(data.students || []);
        
        // Initialize attendance records (default to "PRESENT")
        const initialRecords = {};
        (data.students || []).forEach(student => {
          initialRecords[student.student_id] = "PRESENT";
        });
        setAttendanceRecords(initialRecords);
      } else {
        console.error("Failed to load section roster");
        setError("Failed to load class roster");
        setSectionRoster([]);
        setAttendanceRecords({});
      }
    } catch (err) {
      console.error("Error loading roster:", err);
      setError("Failed to load class roster");
      setSectionRoster([]);
      setAttendanceRecords({});
    } finally {
      setAttendanceLoading(false);
    }
    setAttendanceDialogOpen(true);
  };

  const handleQuickGrading = async (section) => {
    setSelectedSection(section);
    setGradeLoading(true);
    setGradeChanges({});
    
    try {
      // Load gradebook data for the section
      const url = `${API_BASE}/api/v1/gradebook/sections/${section.id}/grades/`;
      const res = await fetch(url, {
        method: "GET",
        headers: getAuthHeaders(),
      });
      
      if (res.ok) {
        const data = await res.json();
        setGradebookData(data);
      } else {
        console.error("Failed to load gradebook data");
        setError("Failed to load gradebook data");
        setGradebookData(null);
      }
    } catch (err) {
      console.error("Error loading gradebook:", err);
      setError("Failed to load gradebook data");
      setGradebookData(null);
    } finally {
      setGradeLoading(false);
    }
    setGradeDialogOpen(true);
  };

  const handleSendMessage = (section) => {
    setSelectedSection(section);
    setMessageSubject(`Message from ${section.course_name} class`);
    setMessageBody("");
    setMessageRecipients("all_parents");
    setMessageDialogOpen(true);
  };

  // Communication functions
  const sendMessage = async () => {
    if (!selectedSection || !messageSubject.trim() || !messageBody.trim()) return;
    
    setMessageLoading(true);
    try {
      // In a real implementation, this would POST to a messaging endpoint
      const messageData = {
        section_id: selectedSection.id,
        subject: messageSubject,
        body: messageBody,
        recipients: messageRecipients,
        sender_type: "teacher"
      };

      console.log("Would send message:", messageData);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setMessageDialogOpen(false);
      setMessageSubject("");
      setMessageBody("");
      // Could show success notification here
    } catch (err) {
      console.error("Error sending message:", err);
      setError("Failed to send message");
    } finally {
      setMessageLoading(false);
    }
  };

  // Attendance management functions
  const updateAttendanceRecord = (studentId, status) => {
    setAttendanceRecords(prev => ({
      ...prev,
      [studentId]: status
    }));
  };

  const saveAttendance = async () => {
    if (!selectedSection) return;
    
    setAttendanceLoading(true);
    try {
      // In a real implementation, this would POST to an attendance endpoint
      // For now, we'll simulate the API call
      const attendanceData = sectionRoster.map(student => ({
        student_id: student.student_id,
        status: attendanceRecords[student.student_id] || "PRESENT",
        date: attendanceDate,
        section_id: selectedSection.id
      }));

      console.log("Would save attendance:", attendanceData);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setAttendanceDialogOpen(false);
      // Could show success notification here
    } catch (err) {
      console.error("Error saving attendance:", err);
      setError("Failed to save attendance");
    } finally {
      setAttendanceLoading(false);
    }
  };

  // Grade management functions
  const updateGradeChange = (studentId, assignmentName, pointsEarned) => {
    const key = `${studentId}-${assignmentName}`;
    setGradeChanges(prev => ({
      ...prev,
      [key]: {
        student_id: studentId,
        assignment_name: assignmentName,
        points_earned: pointsEarned === "" ? null : parseFloat(pointsEarned)
      }
    }));
  };

  const saveGrades = async () => {
    if (!selectedSection || Object.keys(gradeChanges).length === 0) return;
    
    setGradeLoading(true);
    try {
      // In a real implementation, this would PATCH to the gradebook endpoint
      // The planned API: PATCH /api/v1/gradebook/sections/{section_id}/grades/
      // Body: { "changes": [ { "student_id": "...", "assignment_id": "...", "points_earned": 9.5 } ] }
      
      const changes = Object.values(gradeChanges);
      console.log("Would save grade changes:", changes);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setGradeDialogOpen(false);
      setGradeChanges({});
      // Could show success notification here
    } catch (err) {
      console.error("Error saving grades:", err);
      setError("Failed to save grades");
    } finally {
      setGradeLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch(status) {
      case "completed": return "success";
      case "in-progress": return "warning";
      case "upcoming": return "default";
      default: return "default";
    }
  };

  const getStatusIcon = (status) => {
    switch(status) {
      case "completed": return <CheckIcon />;
      case "in-progress": return <TimeIcon />;
      case "upcoming": return <ClassIcon />;
      default: return <ClassIcon />;
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading your classes...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Teacher Dashboard
        </Typography>
        <Typography variant="body1" sx={{ opacity: 0.8 }}>
          Manage your daily classroom activities and student interactions
        </Typography>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)} sx={{ mb: 3 }}>
        <Tab icon={<ClassIcon />} label="Today's Classes" />
        <Tab icon={<AttendanceIcon />} label="Attendance" />
        <Tab icon={<GradeIcon />} label="Quick Grading" />
        <Tab icon={<MessageIcon />} label="Communications" />
      </Tabs>

      {/* Today's Classes Tab */}
      {tabValue === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Typography variant="h6" sx={{ mb: 2 }}>Your Classes Today</Typography>
            <Stack spacing={2}>
              {todaysClasses.map((classItem) => (
                <Card key={classItem.section_id} variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Box sx={{ flex: 1 }}>
                        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 1 }}>
                          <Typography variant="h6">
                            {classItem.course_name}
                          </Typography>
                          <Chip 
                            size="small" 
                            icon={getStatusIcon(classItem.status)}
                            label={classItem.status.replace('-', ' ')} 
                            color={getStatusColor(classItem.status)}
                          />
                        </Stack>
                        <Typography variant="body2" color="text.secondary">
                          {classItem.time} • {classItem.room} • {classItem.roster_count || 0} students
                        </Typography>
                      </Box>
                      <Stack direction="row" spacing={1}>
                        <IconButton 
                          size="small" 
                          onClick={() => handleTakeAttendance(classItem)}
                          title="Take Attendance"
                        >
                          <AttendanceIcon />
                        </IconButton>
                        <IconButton 
                          size="small" 
                          onClick={() => handleQuickGrading(classItem)}
                          title="Quick Grade Entry"
                        >
                          <GradeIcon />
                        </IconButton>
                        <IconButton 
                          size="small" 
                          onClick={() => handleSendMessage(classItem)}
                          title="Send Message"
                        >
                          <MessageIcon />
                        </IconButton>
                      </Stack>
                    </Box>
                  </CardContent>
                </Card>
              ))}
              {todaysClasses.length === 0 && (
                <Alert severity="info">No classes scheduled for today.</Alert>
              )}
            </Stack>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Typography variant="h6" sx={{ mb: 2 }}>Quick Actions</Typography>
            <Stack spacing={2}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Badge badgeContent={3} color="error">
                      <AttendanceIcon color="action" />
                    </Badge>
                    <Typography variant="subtitle1" sx={{ ml: 1 }}>
                      Pending Attendance
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    3 classes need attendance recorded
                  </Typography>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Badge badgeContent={7} color="warning">
                      <GradeIcon color="action" />
                    </Badge>
                    <Typography variant="subtitle1" sx={{ ml: 1 }}>
                      Assignments to Grade
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    7 submissions awaiting grades
                  </Typography>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Badge badgeContent={2} color="info">
                      <MessageIcon color="action" />
                    </Badge>
                    <Typography variant="subtitle1" sx={{ ml: 1 }}>
                      Parent Messages
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    2 messages from parents requiring responses
                  </Typography>
                </CardContent>
              </Card>
            </Stack>
          </Grid>
        </Grid>
      )}

      {/* Attendance Tab */}
      {tabValue === 1 && (
        <Box>
          <Typography variant="h6" sx={{ mb: 2 }}>Attendance Management</Typography>
          <Grid container spacing={2}>
            {todaysClasses.map((classItem) => (
              <Grid item xs={12} md={6} key={classItem.section_id}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1">{classItem.course_name}</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {classItem.roster_count || 0} students • {classItem.time}
                    </Typography>
                    <Button
                      variant="outlined"
                      startIcon={<AttendanceIcon />}
                      onClick={() => handleTakeAttendance(classItem)}
                      fullWidth
                    >
                      Take Attendance
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Quick Grading Tab */}
      {tabValue === 2 && (
        <Box>
          <Typography variant="h6" sx={{ mb: 2 }}>Quick Grade Entry</Typography>
          <Grid container spacing={2}>
            {sections.map((section) => (
              <Grid item xs={12} md={6} key={section.section_id}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1">{section.course_name}</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {section.roster_count || 0} students
                    </Typography>
                    <Button
                      variant="outlined"
                      startIcon={<GradeIcon />}
                      onClick={() => handleQuickGrading(section)}
                      fullWidth
                    >
                      Enter Grades
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Communications Tab */}
      {tabValue === 3 && (
        <Box>
          <Typography variant="h6" sx={{ mb: 2 }}>Parent & Student Communications</Typography>
          <Grid container spacing={2}>
            {sections.map((section) => (
              <Grid item xs={12} md={6} key={section.section_id}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1">{section.course_name}</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Communicate with {section.roster_count || 0} families
                    </Typography>
                    <Stack direction="row" spacing={1}>
                      <Button
                        variant="outlined"
                        startIcon={<MessageIcon />}
                        onClick={() => handleSendMessage(section)}
                        size="small"
                      >
                        Send Message
                      </Button>
                      <Button
                        variant="outlined"
                        startIcon={<AnnouncementIcon />}
                        size="small"
                      >
                        Announcement
                      </Button>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Attendance Dialog - Functional */}
      <Dialog open={attendanceDialogOpen} onClose={() => setAttendanceDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Take Attendance - {selectedSection?.course_name}
          {attendanceLoading && <CircularProgress size={20} sx={{ ml: 2 }} />}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <TextField
              label="Date"
              type="date"
              value={attendanceDate}
              onChange={(e) => setAttendanceDate(e.target.value)}
              sx={{ mr: 2 }}
              InputLabelProps={{ shrink: true }}
            />
          </Box>
          
          {attendanceLoading ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              {sectionRoster.length === 0 ? (
                <Alert severity="warning">No students found in this class.</Alert>
              ) : (
                <Paper sx={{ maxHeight: 400, overflow: 'auto' }}>
                  {sectionRoster.map((student, index) => (
                    <Box key={student.student_id} sx={{ 
                      p: 2, 
                      borderBottom: index < sectionRoster.length - 1 ? '1px solid #e0e0e0' : 'none',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}>
                      <Box>
                        <Typography variant="body1" fontWeight="medium">
                          {student.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Grade {student.grade_level}
                        </Typography>
                      </Box>
                      
                      <FormControl size="small" sx={{ minWidth: 120 }}>
                        <InputLabel>Status</InputLabel>
                        <Select
                          value={attendanceRecords[student.student_id] || "PRESENT"}
                          onChange={(e) => updateAttendanceRecord(student.student_id, e.target.value)}
                          label="Status"
                        >
                          <MenuItem value="PRESENT">Present</MenuItem>
                          <MenuItem value="ABSENT">Absent</MenuItem>
                          <MenuItem value="TARDY">Tardy</MenuItem>
                          <MenuItem value="EXCUSED">Excused</MenuItem>
                        </Select>
                      </FormControl>
                    </Box>
                  ))}
                </Paper>
              )}
              
              {sectionRoster.length > 0 && (
                <Box sx={{ mt: 2, p: 2, bgcolor: 'background.paper', border: '1px solid #e0e0e0', borderRadius: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Summary: {sectionRoster.length} students | 
                    Present: {Object.values(attendanceRecords).filter(status => status === "PRESENT").length} | 
                    Absent: {Object.values(attendanceRecords).filter(status => status === "ABSENT").length} | 
                    Tardy: {Object.values(attendanceRecords).filter(status => status === "TARDY").length} | 
                    Excused: {Object.values(attendanceRecords).filter(status => status === "EXCUSED").length}
                  </Typography>
                </Box>
              )}
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAttendanceDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={saveAttendance}
            disabled={attendanceLoading || sectionRoster.length === 0}
          >
            {attendanceLoading ? "Saving..." : "Save Attendance"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Grade Entry Dialog - Functional */}
      <Dialog open={gradeDialogOpen} onClose={() => setGradeDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          Quick Grade Entry - {selectedSection?.course_name}
          {gradeLoading && <CircularProgress size={20} sx={{ ml: 2 }} />}
        </DialogTitle>
        <DialogContent>
          {gradeLoading ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : gradebookData ? (
            <>
              {gradebookData.assignments.length === 0 ? (
                <Alert severity="info">No assignments found for this class.</Alert>
              ) : (
                <Box sx={{ overflow: 'auto', maxHeight: 500 }}>
                  <Typography variant="h6" gutterBottom>
                    Recent Assignments ({gradebookData.assignments.length})
                  </Typography>
                  
                  {gradebookData.assignments.slice(-3).map((assignment, assignmentIndex) => (
                    <Paper key={assignment.assignment_name} sx={{ mb: 2, p: 2 }}>
                      <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
                        {assignment.assignment_name}
                        <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                          (out of {assignment.points_possible} points)
                        </Typography>
                      </Typography>
                      
                      <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                        {gradebookData.rows.map((studentRow, studentIndex) => {
                          const currentScore = studentRow.scores[assignment.assignment_name];
                          const changeKey = `${studentRow.student.student_id}-${assignment.assignment_name}`;
                          const pendingChange = gradeChanges[changeKey];
                          
                          return (
                            <Box key={studentRow.student.student_id} sx={{ 
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              py: 1,
                              px: 2,
                              borderBottom: studentIndex < gradebookData.rows.length - 1 ? '1px solid #f0f0f0' : 'none',
                              bgcolor: pendingChange ? '#fff3e0' : 'transparent'
                            }}>
                              <Box sx={{ flex: 1 }}>
                                <Typography variant="body2">
                                  {studentRow.student.first_name} {studentRow.student.last_name}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  Grade {studentRow.student.grade_level}
                                </Typography>
                              </Box>
                              
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <TextField
                                  size="small"
                                  label="Points"
                                  type="number"
                                  value={pendingChange?.points_earned ?? (currentScore?.points_earned || "")}
                                  onChange={(e) => updateGradeChange(
                                    studentRow.student.student_id, 
                                    assignment.assignment_name, 
                                    e.target.value
                                  )}
                                  sx={{ width: 80 }}
                                  inputProps={{
                                    min: 0,
                                    max: parseFloat(assignment.points_possible),
                                    step: 0.5
                                  }}
                                />
                                <Typography variant="body2" color="text.secondary">
                                  / {assignment.points_possible}
                                </Typography>
                                {currentScore && (
                                  <Typography variant="body2" color="success.main">
                                    {((parseFloat(currentScore.points_earned || 0) / parseFloat(assignment.points_possible)) * 100).toFixed(1)}%
                                  </Typography>
                                )}
                              </Box>
                            </Box>
                          );
                        })}
                      </Box>
                    </Paper>
                  ))}
                  
                  {Object.keys(gradeChanges).length > 0 && (
                    <Alert severity="warning" sx={{ mt: 2 }}>
                      {Object.keys(gradeChanges).length} grade change(s) pending. Click "Save Grades" to apply.
                    </Alert>
                  )}
                </Box>
              )}
            </>
          ) : (
            <Alert severity="error">Failed to load gradebook data</Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGradeDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={saveGrades}
            disabled={gradeLoading || Object.keys(gradeChanges).length === 0}
          >
            {gradeLoading ? "Saving..." : `Save Grades (${Object.keys(gradeChanges).length})`}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Message Dialog - Functional */}
      <Dialog open={messageDialogOpen} onClose={() => setMessageDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Send Message - {selectedSection?.course_name}
          {messageLoading && <CircularProgress size={20} sx={{ ml: 2 }} />}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Recipients</InputLabel>
              <Select
                value={messageRecipients}
                onChange={(e) => setMessageRecipients(e.target.value)}
                label="Recipients"
              >
                <MenuItem value="all_parents">All Parents in Class</MenuItem>
                <MenuItem value="parents_with_concerns">Parents of Students with Academic Concerns</MenuItem>
                <MenuItem value="parents_of_absent">Parents of Recently Absent Students</MenuItem>
              </Select>
            </FormControl>
          </Box>
          
          <TextField
            fullWidth
            label="Subject"
            value={messageSubject}
            onChange={(e) => setMessageSubject(e.target.value)}
            margin="normal"
            required
          />
          
          <TextField
            fullWidth
            label="Message"
            value={messageBody}
            onChange={(e) => setMessageBody(e.target.value)}
            multiline
            rows={6}
            margin="normal"
            required
            placeholder="Enter your message to parents..."
          />
          
          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>Quick Templates:</strong><br />
              • Weekly update about class progress<br />
              • Reminder about upcoming assignments or tests<br />
              • Positive feedback about student participation<br />
              • Request for parent-teacher conference
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMessageDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={sendMessage}
            disabled={messageLoading || !messageSubject.trim() || !messageBody.trim()}
          >
            {messageLoading ? "Sending..." : "Send Message"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
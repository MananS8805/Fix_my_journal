import React, { useState, useEffect } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Box,
  AppBar,
  Toolbar,
  Typography,
  Stepper,
  Step,
  StepLabel,
  Container,
  Button,
  Alert,
  Divider,
  CircularProgress,
} from '@mui/material';
import axios from 'axios';
import ManuscriptUploader from './components/ManuscriptUploader';
import JournalSelector from './components/JournalSelector';
import FormattingResults from './components/FormattingResults';

// ── MUI Theme ────────────────────────────────────────────────────────────────
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#3B7EFF',
      light: '#6EA8FF',
      dark: '#2D5BE3',
      contrastText: '#fff',
    },
    secondary: {
      main: '#6366F1',
      contrastText: '#fff',
    },
    background: {
      default: '#F4F7FC',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#1A2033',
      secondary: '#7A8BAA',
      disabled: '#B0BECE',
    },
    success: {
      main: '#16A34A',
      light: '#F0FDF4',
      contrastText: '#fff',
    },
    error: {
      main: '#DC2626',
      light: '#FFF5F5',
    },
    warning: {
      main: '#D97706',
      light: '#FFFBEB',
    },
    divider: '#E2EAF4',
  },
  typography: {
    fontFamily: "'Sora', 'Segoe UI', sans-serif",
    h4: { fontFamily: "'Lora', serif", fontWeight: 600, letterSpacing: '-0.3px' },
    h5: { fontFamily: "'Lora', serif", fontWeight: 600 },
    h6: { fontWeight: 700 },
    body2: { color: '#7A8BAA' },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiCssBaseline: {
      styleOverrides: `
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=Lora:ital,wght@0,400;0,600;1,400&family=JetBrains+Mono:wght@400;500&display=swap');
        body { background: #F4F7FC; }
      `,
    },
    MuiCard: {
      styleOverrides: {
        root: {
          border: '1px solid #E2EAF4',
          boxShadow: '0 2px 12px rgba(30,50,100,0.05)',
          borderRadius: 16,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: { borderRadius: 16 },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          textTransform: 'none',
          fontWeight: 600,
          fontFamily: "'Sora', sans-serif",
        },
        containedPrimary: {
          background: 'linear-gradient(135deg, #3B7EFF, #5B6CF6)',
          boxShadow: '0 4px 14px rgba(59,126,255,0.28)',
          '&:hover': {
            boxShadow: '0 8px 22px rgba(59,126,255,0.36)',
            background: 'linear-gradient(135deg, #2D6EEF, #4B5CE6)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontFamily: "'JetBrains Mono', monospace", fontWeight: 500 },
      },
    },
    MuiStepLabel: {
      styleOverrides: {
        label: {
          fontFamily: "'Sora', sans-serif",
          fontWeight: 600,
          fontSize: '0.8rem',
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: { borderRadius: 4 },
      },
    },
    MuiAccordion: {
      styleOverrides: {
        root: {
          border: '1px solid #E2EAF4',
          borderRadius: '12px !important',
          boxShadow: 'none',
          '&:before': { display: 'none' },
          marginBottom: 8,
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        root: { borderRadius: 10 },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          '& fieldset': { borderColor: '#E2EAF4' },
          '&:hover fieldset': { borderColor: '#C7D9FF' },
          '&.Mui-focused fieldset': { borderColor: '#3B7EFF' },
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: { borderRadius: 10, fontSize: '0.825rem' },
      },
    },
  },
});

// ── Constants ────────────────────────────────────────────────────────────────
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';  
const STEPS = ['Upload Manuscript', 'Select Journal', 'Review Results'];

// ── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  const [activeStep, setActiveStep]     = useState(0);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [journals, setJournals]         = useState([]);
  const [selectedJournal, setSelectedJournal] = useState('');
  const [exportFormat, setExportFormat] = useState('docx');
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults]           = useState(null);
  const [error, setError]               = useState(null);

  // Load journal list on mount
  useEffect(() => {
    axios.get(`${API_BASE}/journals`)
      .then(res => {
        if (res.data.success) setJournals(res.data.data.available_journals);
      })
      .catch(err => console.error('Failed to load journals:', err));
  }, []);

  // ── Handlers ──────────────────────────────────────────────────────────────
  const handleFileUpload = (file) => {
    setUploadedFile(file);
    setResults(null);
    setError(null);
    setActiveStep(1);
  };

  const handleFormat = async () => {
    if (!uploadedFile || !selectedJournal) return;
    setIsProcessing(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append('file', uploadedFile);
      const res = await axios.post(
        `${API_BASE}/transform-manuscript`,
        fd,
        {
          params: { journal: selectedJournal },
          headers: { 'Content-Type': 'multipart/form-data' },
        }
      );
      if (res.data.success) {
        setResults(res.data.data);
        setActiveStep(2);
      } else {
        setError(res.data.message || 'Formatting failed.');
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'An unexpected error occurred.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    setUploadedFile(null);
    setSelectedJournal('');
    setExportFormat('docx');
    setResults(null);
    setError(null);
    setActiveStep(0);
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />

      {/* ── Header ── */}
      <AppBar
        position="sticky"
        elevation={0}
        sx={{
          background: '#fff',
          borderBottom: '1px solid #E2EAF4',
          color: 'text.primary',
        }}
      >
        <Toolbar sx={{ px: { xs: 2, sm: 4 }, minHeight: 64 }}>
          <Box sx={{
            width: 34, height: 34, borderRadius: '9px',
            background: 'linear-gradient(135deg, #3B7EFF, #6366F1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            mr: 1.5, flexShrink: 0,
            boxShadow: '0 4px 12px rgba(59,126,255,0.28)',
          }}>
            <Typography sx={{ color: '#fff', fontFamily: "'Lora', serif", fontWeight: 800, fontSize: 15 }}>
              ∂
            </Typography>
          </Box>

          <Box>
            <Typography variant="body1" fontWeight={700} color="text.primary" lineHeight={1.2}>
              Fix My Journal
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ letterSpacing: '1.5px', textTransform: 'uppercase', fontSize: 9 }}>
              Manuscript Formatter
            </Typography>
          </Box>

          <Box sx={{ flexGrow: 1 }} />

          <Box sx={{
            display: 'flex', alignItems: 'center', gap: 0.75,
            px: 1.75, py: 0.6,
            bgcolor: '#F0FDF4', border: '1px solid #BBF7D0', borderRadius: '20px',
          }}>
            <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: '#22C55E',
              animation: 'pulse 2s infinite',
              '@keyframes pulse': { '0%,100%': { opacity: 1 }, '50%': { opacity: 0.35 } }
            }} />
            <Typography variant="caption" sx={{ color: '#16A34A', fontFamily: "'JetBrains Mono', monospace", fontWeight: 500, fontSize: 11 }}>
              API Connected
            </Typography>
          </Box>
        </Toolbar>
      </AppBar>

      {/* ── Main ── */}
      <Container maxWidth="md" sx={{ py: { xs: 3, sm: 5 } }}>

        {activeStep === 0 && (
          <Box sx={{ textAlign: 'center', mb: 5 }}>
            <Box sx={{
              display: 'inline-flex', alignItems: 'center', gap: 0.75,
              px: 1.75, py: 0.7, mb: 2.5,
              bgcolor: '#EEF3FF', border: '1px solid #C7D9FF', borderRadius: '20px',
            }}>
              <Typography sx={{ fontSize: 11, letterSpacing: '2.5px', textTransform: 'uppercase', color: '#3B7EFF', fontFamily: "'JetBrains Mono', monospace", fontWeight: 500 }}>
                ✦ AI-Powered Academic Formatting
              </Typography>
            </Box>
            <Typography variant="h4" sx={{ mb: 1.5, fontSize: { xs: '1.9rem', sm: '2.7rem' } }}>
              Submit with{' '}
              <Box component="em" sx={{ color: 'primary.main', fontStyle: 'italic' }}>confidence.</Box>
              <br />Format in seconds.
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 480, mx: 'auto', lineHeight: 1.75 }}>
              Upload your manuscript and let the system automatically reformat it to meet
              any journal's exact submission guidelines.
            </Typography>
          </Box>
        )}

        <Stepper
          activeStep={activeStep}
          alternativeLabel
          sx={{
            mb: 4,
            '& .MuiStepConnector-line': { borderColor: '#E2EAF4', borderTopWidth: 2 },
            '& .MuiStepConnector-root.Mui-completed .MuiStepConnector-line': { borderColor: 'primary.main' },
            '& .MuiStepIcon-root': { color: '#DDE4EF' },
            '& .MuiStepIcon-root.Mui-active': { color: 'primary.main' },
            '& .MuiStepIcon-root.Mui-completed': { color: 'primary.main' },
          }}
        >
          {STEPS.map(label => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Step 0: Upload */}
        {activeStep === 0 && (
          <ManuscriptUploader
            onFileUpload={handleFileUpload}
            isProcessing={isProcessing}
            uploadedFile={uploadedFile}
          />
        )}

        {/* Step 1: Configure */}
        {activeStep === 1 && (
          <Box>
            <JournalSelector
              journals={journals}
              selectedJournal={selectedJournal}
              onJournalChange={setSelectedJournal}
              exportFormat={exportFormat}
              onExportFormatChange={setExportFormat}
            />

            <Divider sx={{ my: 3, borderColor: '#E2EAF4' }} />

            <Box sx={{ display: 'flex', gap: 1.5 }}>
              <Button
                variant="outlined"
                onClick={() => setActiveStep(0)}
                sx={{ borderColor: '#E2EAF4', color: 'text.secondary', '&:hover': { borderColor: '#C7D9FF', bgcolor: '#F4F7FF' } }}
              >
                ← Back
              </Button>
              <Button
                variant="contained"
                color="primary"
                fullWidth
                disabled={!selectedJournal || isProcessing}
                onClick={handleFormat}
                sx={{ py: 1.5, fontSize: '0.9rem' }}
              >
                {isProcessing
                  ? <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><CircularProgress size={18} sx={{ color: '#fff' }} /> Formatting…</Box>
                  : `Format for ${journals.find(j => j.id === selectedJournal)?.name || '…'} & Export as ${exportFormat.toUpperCase()} →`
                }
              </Button>
            </Box>
          </Box>
        )}

        {/* Step 2: Results */}
        {activeStep === 2 && (
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Box>
                <Typography variant="caption" sx={{ color: '#9AAAC4', letterSpacing: '1.5px', textTransform: 'uppercase', fontFamily: "'JetBrains Mono', monospace" }}>
                  Formatting complete
                </Typography>
                <Typography variant="h5" sx={{ color: 'text.primary' }}>
                  Ready for{' '}
                  <Box component="em" sx={{ color: 'primary.main' }}>
                    {results?.journal || selectedJournal}
                  </Box>
                </Typography>
              </Box>
              <Button variant="outlined" onClick={handleReset}
                sx={{ borderColor: '#E2EAF4', color: 'text.secondary', whiteSpace: 'nowrap', '&:hover': { borderColor: '#C7D9FF' } }}>
                Format Another
              </Button>
            </Box>

            <FormattingResults
              results={results}
              selectedJournal={selectedJournal}
              uploadedFile={uploadedFile}
            />
          </Box>
        )}

      </Container>

      {/* ── Footer ── */}
      <Box component="footer" sx={{
        mt: 'auto', py: 2.5, px: 4,
        borderTop: '1px solid #E2EAF4', bgcolor: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <Typography variant="caption" color="text.secondary">
          Fix My Journal — Manuscript Formatting Agent
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ fontFamily: "'JetBrains Mono', monospace" }}>
          FastAPI · Docling · Google AI
        </Typography>
      </Box>
    </ThemeProvider>
  );
}
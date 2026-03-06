import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Container, Box, Typography, Paper } from '@mui/material';
import ManuscriptUploader from './components/ManuscriptUploader';
import JournalSelector from './components/JournalSelector';
import FormattingResults from './components/FormattingResults';
import axios from 'axios';

const API = axios.create({
  baseURL: "http://localhost:8001"
});

const theme = createTheme({
  palette: {
    primary: { main: '#1976d2' },
    secondary: { main: '#dc004e' }
  }
});

function App() {

  const [journals, setJournals] = useState([]);
  const [selectedJournal, setSelectedJournal] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);

  useEffect(() => {
    loadJournals();
  }, []);

  const loadJournals = async () => {
    try {
      const response = await API.get('/journals');
      if (response.data.success) {
        setJournals(response.data.data.available_journals);
      }
    } catch (error) {
      console.error('Error loading journals:', error);
    }
  };

  const handleFormatManuscript = async (file) => {

    if (!selectedJournal) {
      alert("Please select a journal first");
      return;
    }

    setUploadedFile(file);
    setLoading(true);

    try {

      const formData = new FormData();
      formData.append("file", file);

      const response = await API.post(
        "/transform-manuscript",
        formData,
        {
          params: {
            journal: selectedJournal
          }
        }
      );

      if (response.data.success) {
        setResults(response.data.data);
      }

    } catch (error) {
      console.error("Formatting error:", error);
      alert("Formatting failed.");
    }

    setLoading(false);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />

      <Container maxWidth="lg">

        <Box sx={{ my: 4 }}>

          <Typography variant="h3" align="center">
            AI Manuscript Formatting Agent
          </Typography>

          <Typography variant="h6" align="center" color="text.secondary">
            Automatically format research papers for journal submission
          </Typography>

          <Paper elevation={3} sx={{ p: 3, mt: 4 }}>

            <JournalSelector
              journals={journals}
              selectedJournal={selectedJournal}
              onJournalChange={setSelectedJournal}
            />

            <ManuscriptUploader
              onFileUpload={handleFormatManuscript}
              isProcessing={loading}
              uploadedFile={uploadedFile}
            />

            <FormattingResults
              results={results}
              selectedJournal={selectedJournal}
              uploadedFile={uploadedFile}
            />

          </Paper>

        </Box>

      </Container>
    </ThemeProvider>
  );
}

export default App; 

import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Paper,
  Alert
} from '@mui/material';
import { ExpandMore, Download, Info } from '@mui/icons-material';

const FormattingResults = ({ results, selectedJournal, uploadedFile }) => {
  if (!results) {
    return null;
  }

  const apiBaseUrl = 'http://localhost:8001';
  const journalId = selectedJournal || (results.journal ? results.journal.toLowerCase() : '');
  const filePath = results.file_path || '';
  const fileName = filePath ? filePath.split(/[/\\]/).pop() : '';
  const downloadUrl = results.download_url
    ? `${apiBaseUrl}${results.download_url}`
    : (fileName && journalId
        ? `${apiBaseUrl}/export-file/${journalId}/${encodeURIComponent(fileName)}`
        : null);

  const changes = Array.isArray(results.changelog) ? results.changelog : [];

  const severityColor = (severity) => {
    const value = (severity || '').toLowerCase();
    if (value === 'critical' || value === 'high' || value === 'error') return 'error';
    if (value === 'warning' || value === 'medium') return 'warning';
    return 'info';
  };

  const handleDownload = async () => {
    if (!downloadUrl) return;

    try {
      const response = await fetch(downloadUrl);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = fileName || 'download.docx';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
      // Optionally, show an error message to the user
    }
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        Formatting Results
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Summary
          </Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Uploaded File
              </Typography>
              <Typography variant="body2">
                {uploadedFile ? uploadedFile.name : 'N/A'}
              </Typography>
            </Grid>

            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Selected Journal
              </Typography>
              <Typography variant="body2">
                {results.journal || journalId || 'N/A'}
              </Typography>
            </Grid>

            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Export Format
              </Typography>
              <Typography variant="body2">
                {results.export_format ? results.export_format.toUpperCase() : 'DOCX'}
              </Typography>
            </Grid>

            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Export File
              </Typography>
              <Typography variant="body2">
                {fileName || filePath || 'N/A'}
              </Typography>
            </Grid>

            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Total Changes
              </Typography>
              <Typography variant="body2">
                {typeof results.total_changes === 'number' ? results.total_changes : changes.length}
              </Typography>
            </Grid>

            {results.metadata && (
              <>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Abstract Length
                  </Typography>
                  <Typography variant="body2">
                    {results.metadata.abstract_length ?? 'N/A'}
                  </Typography>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Page Limit
                  </Typography>
                  <Typography variant="body2">
                    {results.metadata.page_limit ?? 'No limit'}
                  </Typography>
                </Grid>
              </>
            )}
          </Grid>
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Download Exported File
          </Typography>

          {downloadUrl ? (
            <Button
              variant="contained"
              startIcon={<Download />}
              onClick={handleDownload}
            >
              Download {results.export_format ? results.export_format.toUpperCase() : 'File'}
            </Button>
          ) : (
            <Alert severity="warning">
              Export file not available yet.
            </Alert>
          )}
        </CardContent>
      </Card>

      {results.changelog_markdown && (
        <Card sx={{ mb: 3, bgcolor: 'grey.50' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Changelog Summary
            </Typography>
            <Typography
              variant="body2"
              sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.875rem' }}
            >
              {results.changelog_markdown}
            </Typography>
          </CardContent>
        </Card>
      )}

      {changes.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Changes Made
            </Typography>

            <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
              {changes.map((change, index) => (
                <Accordion key={index} sx={{ mb: 1 }}>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Info color="info" />
                      <Typography variant="body2">
                        {change.category || 'Change'}: {change.change_type || 'update'}
                      </Typography>
                      <Chip
                        label={change.severity || 'info'}
                        size="small"
                        color={severityColor(change.severity)}
                      />
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    {change.reason && (
                      <Typography variant="body2" color="text.secondary">
                        {change.reason}
                      </Typography>
                    )}

                    {(change.old_value || change.new_value) && (
                      <Grid container spacing={2} sx={{ mt: 1 }}>
                        <Grid item xs={12} md={6}>
                          <Typography variant="body2" fontWeight="bold">
                            Original
                          </Typography>
                          <Paper sx={{ p: 1, bgcolor: 'grey.100', fontSize: '0.875rem' }}>
                            {change.old_value || 'N/A'}
                          </Paper>
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <Typography variant="body2" fontWeight="bold">
                            Formatted
                          </Typography>
                          <Paper sx={{ p: 1, bgcolor: 'success.50', fontSize: '0.875rem' }}>
                            {change.new_value || 'N/A'}
                          </Paper>
                        </Grid>
                      </Grid>
                    )}
                  </AccordionDetails>
                </Accordion>
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      {Array.isArray(results.correction_log) && results.correction_log.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Compliance Report
            </Typography>
            {results.correction_log.map((entry, index) => (
              <Typography variant="body2" key={index} sx={{ mb: 1 }}>
                {entry}
              </Typography>
            ))}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default FormattingResults;

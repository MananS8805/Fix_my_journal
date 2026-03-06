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
  Alert,
  Divider,
  LinearProgress,
} from '@mui/material';
import { ExpandMore, Download, Info, CheckCircle, Cancel, Warning } from '@mui/icons-material';

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
    : fileName && journalId
    ? `${apiBaseUrl}/export-file/${journalId}/${encodeURIComponent(fileName)}`
    : null;

  const changes = Array.isArray(results.changelog) ? results.changelog : [];
  const correctionLog = Array.isArray(results.correction_log) ? results.correction_log : [];
  const discoveredRules = results.discovered_rules || null;
  const citationValidation = results.citation_validation || null;
  const transformValidation = results.transformation_validation || null;
  const compliance = results.compliance || null;

  const severityColor = (severity) => {
    const value = (severity || '').toLowerCase();
    if (value === 'critical' || value === 'high' || value === 'error') return 'error';
    if (value === 'warning' || value === 'medium') return 'warning';
    return 'info';
  };

  const complianceSeverityColor = (severity) => {
    if (severity === 'high') return 'error';
    if (severity === 'medium') return 'warning';
    if (severity === 'low') return 'warning';
    if (severity === 'info') return 'info';
    return 'warning';
  };

  const handleDownload = async () => {
    if (!downloadUrl) return;
    try {
      const response = await fetch(downloadUrl);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = fileName || 'manuscript.docx';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed. Please try again.');
    }
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h5" gutterBottom fontWeight="bold">
        Formatting Results
      </Typography>

      {/* ── Summary Card ─────────────────────────────────── */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Summary</Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">Uploaded File</Typography>
              <Typography variant="body2">{uploadedFile ? uploadedFile.name : 'N/A'}</Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">Target Journal</Typography>
              <Typography variant="body2">{results.journal || journalId || 'N/A'}</Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">Export Format</Typography>
              <Typography variant="body2">
                {results.export_format ? results.export_format.toUpperCase() : 'DOCX'}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">Output File</Typography>
              <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                {fileName || 'N/A'}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* ── Download Card ──────────────────────────────────── */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Download Formatted Manuscript</Typography>
          {downloadUrl ? (
            <Button
              variant="contained"
              color="success"
              startIcon={<Download />}
              onClick={handleDownload}
              size="large"
            >
              Download {results.export_format ? results.export_format.toUpperCase() : 'DOCX'}
            </Button>
          ) : (
            <Alert severity="warning">Export file not available. Check server logs.</Alert>
          )}
        </CardContent>
      </Card>

      {/* ── Compliance Report ─────────────────────────────── */}
      {compliance && !compliance.error && (
        <Card sx={{ mb: 3, border: '1px solid', borderColor: compliance.score >= 80 ? 'success.light' : compliance.score >= 50 ? 'warning.light' : 'error.light' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">
                Compliance Report — {compliance.journal}
              </Typography>
              <Chip
                label={`Score: ${compliance.score}%`}
                color={compliance.score >= 80 ? 'success' : compliance.score >= 50 ? 'warning' : 'error'}
                size="medium"
                sx={{ fontWeight: 'bold', fontSize: '0.9rem' }}
              />
            </Box>

            {/* Score bar */}
            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                <Typography variant="caption" color="text.secondary">
                  {compliance.passed_checks} of {compliance.total_checks} checks passed
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {compliance.score}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={compliance.score}
                color={compliance.score >= 80 ? 'success' : compliance.score >= 50 ? 'warning' : 'error'}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>

            {/* Warnings — things to fix */}
            {(compliance.warnings || []).filter(w => w.severity !== 'info').length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                  ⚠️ Action Required
                </Typography>
                {compliance.warnings
                  .filter(w => w.severity !== 'info')
                  .map((w, i) => (
                    <Alert
                      key={i}
                      severity={complianceSeverityColor(w.severity)}
                      sx={{ mb: 1 }}
                      icon={<Warning fontSize="small" />}
                    >
                      <strong>{w.check}:</strong> {w.message}
                    </Alert>
                  ))}
              </Box>
            )}

            {/* Info notices — auto-applied formatting */}
            {(compliance.warnings || []).filter(w => w.severity === 'info').length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                  ℹ️ Applied Automatically
                </Typography>
                {compliance.warnings
                  .filter(w => w.severity === 'info')
                  .map((w, i) => (
                    <Alert key={i} severity="info" sx={{ mb: 1 }}>
                      <strong>{w.check}:</strong> {w.message}
                    </Alert>
                  ))}
              </Box>
            )}

            {/* Passes — what's correct */}
            {(compliance.passes || []).length > 0 && (
              <Accordion sx={{ mt: 1 }}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CheckCircle color="success" fontSize="small" />
                    <Typography variant="subtitle2">
                      {compliance.passes.length} checks passed — click to expand
                    </Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  {compliance.passes.map((p, i) => (
                    <Alert key={i} severity="success" sx={{ mb: 1 }}>
                      <strong>{p.check}:</strong> {p.message}
                    </Alert>
                  ))}
                </AccordionDetails>
              </Accordion>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Processing Log ─────────────────────────────────── */}
      {correctionLog.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Processing Log</Typography>
            <Box sx={{ maxHeight: 220, overflow: 'auto', bgcolor: 'grey.50', borderRadius: 1, p: 1 }}>
              {correctionLog.map((entry, index) => (
                <Typography key={index} variant="body2" sx={{ mb: 0.5, display: 'flex', gap: 1 }}>
                  <span style={{ color: '#888', minWidth: 24 }}>{index + 1}.</span>
                  {entry}
                </Typography>
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* ── Discovered Journal Rules ───────────────────────── */}
      {discoveredRules && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Discovered Journal Rules</Typography>
            <Grid container spacing={1}>
              {Object.entries(discoveredRules)
                .filter(([k]) => !['journal', 'source_url', 'status', 'raw_output'].includes(k))
                .map(([key, value]) => (
                  <Grid item xs={6} md={4} key={key}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                    </Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {String(value)}
                    </Typography>
                  </Grid>
                ))}
            </Grid>
            {discoveredRules.source_url && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Source: {discoveredRules.source_url}
              </Typography>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Citation Validation ───────────────────────────── */}
      {citationValidation && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <Typography variant="h6">Citation Validation</Typography>
              {citationValidation.valid ? (
                <CheckCircle color="success" />
              ) : (
                <Cancel color="error" />
              )}
              <Chip
                label={citationValidation.valid ? 'Valid' : 'Issues Found'}
                color={citationValidation.valid ? 'success' : 'error'}
                size="small"
              />
            </Box>
            <Grid container spacing={2}>
              <Grid item xs={6} md={3}>
                <Typography variant="caption" color="text.secondary">Citations in Text</Typography>
                <Typography variant="body2">{citationValidation.total_citations_in_text ?? 'N/A'}</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="caption" color="text.secondary">References in List</Typography>
                <Typography variant="body2">{citationValidation.total_references_in_list ?? 'N/A'}</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="caption" color="text.secondary">Missing</Typography>
                <Typography variant="body2" color="error.main">
                  {(citationValidation.missing_references || []).length}
                </Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="caption" color="text.secondary">Unused</Typography>
                <Typography variant="body2" color="warning.main">
                  {(citationValidation.unused_references || []).length}
                </Typography>
              </Grid>
            </Grid>
            {(citationValidation.suggestions || []).length > 0 && (
              <Box sx={{ mt: 2 }}>
                {citationValidation.suggestions.map((s, i) => (
                  <Alert key={i} severity={s.issue === 'Missing Reference' ? 'error' : 'warning'} sx={{ mb: 1 }}>
                    <strong>{s.issue}:</strong> {s.suggestion}
                  </Alert>
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Transformation Sanity Check ───────────────────── */}
      {transformValidation && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <Typography variant="h6">Document Integrity Check</Typography>
              {transformValidation.is_sane ? (
                <CheckCircle color="success" />
              ) : (
                <Cancel color="warning" />
              )}
            </Box>
            <Grid container spacing={2}>
              <Grid item xs={6} md={3}>
                <Typography variant="caption" color="text.secondary">Source Words</Typography>
                <Typography variant="body2">{transformValidation.original_word_count}</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="caption" color="text.secondary">DOCX Words</Typography>
                <Typography variant="body2">{transformValidation.docx_word_count}</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="caption" color="text.secondary">Source Headings</Typography>
                <Typography variant="body2">{transformValidation.original_heading_count}</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="caption" color="text.secondary">DOCX Headings</Typography>
                <Typography variant="body2">{transformValidation.docx_heading_count}</Typography>
              </Grid>
            </Grid>
            <Typography variant="body2" sx={{ mt: 1 }} color={transformValidation.is_sane ? 'success.main' : 'warning.main'}>
              {transformValidation.suggestion}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* ── Detailed Changes ──────────────────────────────── */}
      {changes.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Formatting Changes ({changes.length})
            </Typography>
            <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
              {changes.map((change, index) => (
                <Accordion key={index} sx={{ mb: 1 }}>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                      <Info color="info" fontSize="small" />
                      <Typography variant="body2">
                        {change.category || 'Change'} — {change.change_type || 'update'}
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
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {change.reason}
                      </Typography>
                    )}
                    {(change.old_value || change.new_value) && (
                      <Grid container spacing={2}>
                        <Grid item xs={12} md={6}>
                          <Typography variant="body2" fontWeight="bold">Original</Typography>
                          <Paper sx={{ p: 1, bgcolor: 'grey.100', fontSize: '0.85rem' }}>
                            {change.old_value || 'N/A'}
                          </Paper>
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <Typography variant="body2" fontWeight="bold">Formatted</Typography>
                          <Paper sx={{ p: 1, bgcolor: 'success.50', fontSize: '0.85rem' }}>
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
    </Box>
  );
};

export default FormattingResults;
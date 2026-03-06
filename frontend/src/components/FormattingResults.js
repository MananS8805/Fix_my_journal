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
  LinearProgress,
} from '@mui/material';
import {
  ExpandMore,
  Download,
  Info,
  CheckCircle,
  Cancel,
  Warning,
} from '@mui/icons-material';

// ── Helpers ──────────────────────────────────────────────────────────────────
const severityColor = (severity) => {
  const v = (severity || '').toLowerCase();
  if (v === 'critical' || v === 'high' || v === 'error') return 'error';
  if (v === 'warning' || v === 'medium') return 'warning';
  return 'info';
};

const complianceSeverityColor = (severity) => {
  if (severity === 'high')   return 'error';
  if (severity === 'medium') return 'warning';
  if (severity === 'low')    return 'warning';
  if (severity === 'info')   return 'info';
  return 'warning';
};

const scoreColor = (score) =>
  score >= 80 ? 'success' : score >= 50 ? 'warning' : 'error';

// ── Score ring (SVG) ─────────────────────────────────────────────────────────
function ScoreRing({ score }) {
  const r = 36, circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 80 ? '#3B7EFF' : score >= 50 ? '#D97706' : '#DC2626';
  return (
    <Box sx={{ position: 'relative', width: 96, height: 96, display: 'flex', alignItems: 'center', justifyContent: 'center', mx: 'auto', mb: 1 }}>
      <svg width="96" height="96" style={{ transform: 'rotate(-90deg)', position: 'absolute' }}>
        <circle cx="48" cy="48" r={r} fill="none" stroke="#E8EEF8" strokeWidth="7" />
        <circle cx="48" cy="48" r={r} fill="none" stroke={color} strokeWidth="7"
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s ease' }} />
      </svg>
      <Box sx={{ textAlign: 'center', zIndex: 1 }}>
        <Typography sx={{ fontSize: 22, fontWeight: 700, color, fontFamily: "'JetBrains Mono', monospace", lineHeight: 1 }}>
          {score}
        </Typography>
        <Typography sx={{ fontSize: 9, color: '#9AAAC4', letterSpacing: 1, textTransform: 'uppercase' }}>
          Score
        </Typography>
      </Box>
    </Box>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
const FormattingResults = ({ results, selectedJournal, uploadedFile }) => {
  if (!results) return null;

  const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8001';
  const journalId     = selectedJournal || (results.journal ? results.journal.toLowerCase() : '');
  const filePath      = results.file_path || '';
  const fileName      = filePath ? filePath.split(/[/\\]/).pop() : '';
  const downloadUrl   = results.download_url
    ? `${apiBaseUrl}${results.download_url}`
    : fileName && journalId
    ? `${apiBaseUrl}/export-file/${journalId}/${encodeURIComponent(fileName)}`
    : null;

  const changes           = Array.isArray(results.changelog)       ? results.changelog       : [];
  const correctionLog     = Array.isArray(results.correction_log)  ? results.correction_log  : [];
  const discoveredRules   = results.discovered_rules   || null;
  const citationValidation  = results.citation_validation    || null;
  const transformValidation = results.transformation_validation || null;
  const compliance        = results.compliance || null;

  const handleDownload = async () => {
    if (!downloadUrl) return;
    try {
      const response = await fetch(downloadUrl);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const blob = await response.blob();
      const url  = window.URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.href     = url;
      a.download = fileName || 'manuscript.docx';
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Download failed:', err);
      alert('Download failed. Please try again.');
    }
  };

  return (
    <Box sx={{ mt: 3 }}>

      {/* ── Summary + Compliance side-by-side ─────────────────────────────── */}
      <Grid container spacing={2} sx={{ mb: 2.5 }}>

        {/* Summary */}
        <Grid item xs={12} md={compliance ? 7 : 12}>
          <Card elevation={0}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>Summary</Typography>
              <Grid container spacing={2}>
                {[
                  { label: 'Uploaded File',  value: uploadedFile?.name || 'N/A' },
                  { label: 'Target Journal', value: results.journal || journalId || 'N/A' },
                  { label: 'Export Format',  value: results.export_format ? results.export_format.toUpperCase() : 'DOCX' },
                  { label: 'Output File',    value: fileName || 'N/A' },
                ].map(({ label, value }) => (
                  <Grid item xs={6} key={label}>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.3 }}>
                      {label}
                    </Typography>
                    <Typography variant="body2" fontWeight={500} color="text.primary" sx={{ wordBreak: 'break-all' }}>
                      {value}
                    </Typography>
                  </Grid>
                ))}
              </Grid>

              {/* Download button inside summary */}
              <Box sx={{ mt: 2.5 }}>
                {downloadUrl ? (
                  <Button
                    variant="contained"
                    startIcon={<Download />}
                    onClick={handleDownload}
                    sx={{
                      bgcolor: '#F0FDF4', color: '#16A34A',
                      border: '1.5px solid #BBF7D0',
                      boxShadow: 'none',
                      '&:hover': { bgcolor: '#DCFCE7', boxShadow: 'none' },
                    }}
                  >
                    Download {results.export_format ? results.export_format.toUpperCase() : 'DOCX'}
                  </Button>
                ) : (
                  <Alert severity="warning" sx={{ py: 0.5 }}>
                    Export file not available. Check server logs.
                  </Alert>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Compliance score ring */}
        {compliance && !compliance.error && (
          <Grid item xs={12} md={5}>
            <Card elevation={0} sx={{
              height: '100%',
              border: '1px solid',
              borderColor: compliance.score >= 80 ? '#BBF7D0' : compliance.score >= 50 ? '#FDE68A' : '#FECACA',
            }}>
              <CardContent sx={{ p: 3, textAlign: 'center' }}>
                <Typography variant="h6" gutterBottom>Compliance Score</Typography>
                <ScoreRing score={compliance.score} />
                <Chip
                  label={`${compliance.score}%`}
                  color={scoreColor(compliance.score)}
                  sx={{ fontWeight: 700, fontSize: '0.85rem', mb: 1.5 }}
                />
                <Box sx={{ mb: 1.5 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="caption" color="text.secondary">
                      {compliance.passed_checks} / {compliance.total_checks} checks passed
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {compliance.score}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={compliance.score}
                    color={scoreColor(compliance.score)}
                    sx={{ height: 7, borderRadius: 4 }}
                  />
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {compliance.journal}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* ── Compliance Warnings ───────────────────────────────────────────── */}
      {compliance && !compliance.error && (
        <Card elevation={0} sx={{ mb: 2.5 }}>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Compliance Details</Typography>

            {(compliance.warnings || []).filter(w => w.severity !== 'info').length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                  ⚠️ Action Required
                </Typography>
                {compliance.warnings.filter(w => w.severity !== 'info').map((w, i) => (
                  <Alert key={i} severity={complianceSeverityColor(w.severity)} sx={{ mb: 1 }} icon={<Warning fontSize="small" />}>
                    <strong>{w.check}:</strong> {w.message}
                  </Alert>
                ))}
              </Box>
            )}

            {(compliance.warnings || []).filter(w => w.severity === 'info').length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                  ℹ️ Applied Automatically
                </Typography>
                {compliance.warnings.filter(w => w.severity === 'info').map((w, i) => (
                  <Alert key={i} severity="info" sx={{ mb: 1 }}>
                    <strong>{w.check}:</strong> {w.message}
                  </Alert>
                ))}
              </Box>
            )}

            {(compliance.passes || []).length > 0 && (
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CheckCircle color="success" fontSize="small" />
                    <Typography variant="subtitle2">
                      {compliance.passes.length} checks passed — expand to view
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

      {/* ── Processing Log ────────────────────────────────────────────────── */}
      {correctionLog.length > 0 && (
        <Card elevation={0} sx={{ mb: 2.5 }}>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Processing Log</Typography>
            <Box sx={{
              maxHeight: 220, overflow: 'auto',
              bgcolor: '#F8FAFC', border: '1px solid #E2EAF4',
              borderRadius: '12px', p: 2,
            }}>
              {correctionLog.map((entry, i) => (
                <Typography key={i} variant="body2" sx={{ mb: 0.5, display: 'flex', gap: 1, fontFamily: "'JetBrains Mono', monospace", fontSize: '0.78rem' }}>
                  <Box component="span" sx={{ color: '#9AAAC4', minWidth: 24 }}>{i + 1}.</Box>
                  <Box component="span" sx={{ color: '#4A5568' }}>{entry}</Box>
                </Typography>
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* ── Discovered Journal Rules ──────────────────────────────────────── */}
      {discoveredRules && (
        <Card elevation={0} sx={{ mb: 2.5 }}>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Discovered Journal Rules</Typography>
            <Grid container spacing={1.5}>
              {Object.entries(discoveredRules)
                .filter(([k]) => !['journal', 'source_url', 'status', 'raw_output'].includes(k))
                .map(([key, value]) => (
                  <Grid item xs={6} md={4} key={key}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                    </Typography>
                    <Typography variant="body2" fontWeight={600} color="text.primary">
                      {String(value)}
                    </Typography>
                  </Grid>
                ))}
            </Grid>
            {discoveredRules.source_url && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1.5, display: 'block' }}>
                Source: {discoveredRules.source_url}
              </Typography>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Citation Validation ───────────────────────────────────────────── */}
      {citationValidation && (
        <Card elevation={0} sx={{ mb: 2.5 }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <Typography variant="h6">Citation Validation</Typography>
              {citationValidation.valid ? <CheckCircle color="success" /> : <Cancel color="error" />}
              <Chip
                label={citationValidation.valid ? 'Valid' : 'Issues Found'}
                color={citationValidation.valid ? 'success' : 'error'}
                size="small"
              />
            </Box>

            <Grid container spacing={2} sx={{ mb: 2 }}>
              {[
                { label: 'Citations in Text',   value: citationValidation.total_citations_in_text  ?? 'N/A', color: 'text.primary' },
                { label: 'References in List',  value: citationValidation.total_references_in_list ?? 'N/A', color: 'text.primary' },
                { label: 'Missing',             value: (citationValidation.missing_references || []).length, color: 'error.main' },
                { label: 'Unused',              value: (citationValidation.unused_references  || []).length, color: 'warning.main' },
              ].map(({ label, value, color }) => (
                <Grid item xs={6} md={3} key={label}>
                  <Box sx={{ p: 1.5, bgcolor: '#F8FAFC', border: '1px solid #E2EAF4', borderRadius: '10px', textAlign: 'center' }}>
                    <Typography variant="caption" color="text.secondary" display="block">{label}</Typography>
                    <Typography variant="h6" sx={{ color, fontFamily: "'JetBrains Mono', monospace" }}>{value}</Typography>
                  </Box>
                </Grid>
              ))}
            </Grid>

            {(citationValidation.suggestions || []).map((s, i) => (
              <Alert key={i} severity={s.issue === 'Missing Reference' ? 'error' : 'warning'} sx={{ mb: 1 }}>
                <strong>{s.issue}:</strong> {s.suggestion}
              </Alert>
            ))}
          </CardContent>
        </Card>
      )}

      {/* ── Transformation Integrity Check ────────────────────────────────── */}
      {transformValidation && (
        <Card elevation={0} sx={{ mb: 2.5 }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <Typography variant="h6">Document Integrity Check</Typography>
              {transformValidation.is_sane ? <CheckCircle color="success" /> : <Cancel color="warning" />}
            </Box>

            <Grid container spacing={2} sx={{ mb: 1.5 }}>
              {[
                { label: 'Source Words',    value: transformValidation.original_word_count },
                { label: 'DOCX Words',      value: transformValidation.docx_word_count },
                { label: 'Source Headings', value: transformValidation.original_heading_count },
                { label: 'DOCX Headings',   value: transformValidation.docx_heading_count },
              ].map(({ label, value }) => (
                <Grid item xs={6} md={3} key={label}>
                  <Box sx={{ p: 1.5, bgcolor: '#F8FAFC', border: '1px solid #E2EAF4', borderRadius: '10px', textAlign: 'center' }}>
                    <Typography variant="caption" color="text.secondary" display="block">{label}</Typography>
                    <Typography variant="h6" sx={{ fontFamily: "'JetBrains Mono', monospace", color: 'text.primary' }}>{value}</Typography>
                  </Box>
                </Grid>
              ))}
            </Grid>

            <Typography variant="body2" color={transformValidation.is_sane ? 'success.main' : 'warning.main'}>
              {transformValidation.suggestion}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* ── Detailed Changes ──────────────────────────────────────────────── */}
      {changes.length > 0 && (
        <Card elevation={0} sx={{ mb: 2 }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">Formatting Changes</Typography>
              <Chip
                label={`${changes.length} changes`}
                size="small"
                sx={{ bgcolor: '#EEF3FF', color: 'primary.main', border: '1px solid #C7D9FF', fontFamily: "'JetBrains Mono', monospace" }}
              />
            </Box>

            <Box sx={{ maxHeight: 420, overflow: 'auto' }}>
              {changes.map((change, i) => (
                <Accordion key={i}>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                      <Info color="info" fontSize="small" />
                      <Typography variant="body2" fontWeight={500}>
                        {change.category || 'Change'} — {change.change_type || 'update'}
                      </Typography>
                      <Chip
                        label={change.severity || 'info'}
                        size="small"
                        color={severityColor(change.severity)}
                        sx={{ fontSize: 10 }}
                      />
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails sx={{ pt: 0 }}>
                    {change.reason && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5, fontStyle: 'italic' }}>
                        {change.reason}
                      </Typography>
                    )}
                    {(change.old_value || change.new_value) && (
                      <Grid container spacing={2}>
                        <Grid item xs={12} md={6}>
                          <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                            Original
                          </Typography>
                          <Paper elevation={0} sx={{ p: 1.5, bgcolor: '#FFF5F5', border: '1px solid #FECACA', borderRadius: '10px', fontSize: '0.82rem', fontFamily: "'JetBrains Mono', monospace", color: '#7F1D1D' }}>
                            {change.old_value || 'N/A'}
                          </Paper>
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                            Formatted
                          </Typography>
                          <Paper elevation={0} sx={{ p: 1.5, bgcolor: '#F0FDF4', border: '1px solid #BBF7D0', borderRadius: '10px', fontSize: '0.82rem', fontFamily: "'JetBrains Mono', monospace", color: '#14532D' }}>
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

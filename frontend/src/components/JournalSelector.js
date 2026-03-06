import React, { useState, useEffect } from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
} from '@mui/material';
import axios from 'axios';

const EXPORT_FORMATS = [
  { id: 'docx', icon: '📝', label: 'Word', desc: 'Easy to edit' },
  { id: 'latex', icon: '⌨️', label: 'LaTeX', desc: 'For typesetting' },
  { id: 'pdf',  icon: '📄', label: 'PDF',   desc: 'Print-ready' },
];

const JournalSelector = ({
  journals,
  selectedJournal,
  onJournalChange,
  exportFormat,
  onExportFormatChange,
}) => {
  const [journalDetails, setJournalDetails] = useState(null);

  useEffect(() => {
    if (selectedJournal) {
      loadJournalDetails(selectedJournal);
    } else {
      setJournalDetails(null);
    }
  }, [selectedJournal]);

  const loadJournalDetails = async (journalId) => {
    try {
      const response = await axios.get(`http://localhost:8001/journals/${journalId}`);
      if (response.data.success) setJournalDetails(response.data.data);
    } catch (error) {
      console.error('Error loading journal details:', error);
    }
  };

  return (
    <Box sx={{ mb: 2 }}>
      <Grid container spacing={2.5}>

        {/* ── Journal Picker ── */}
        <Grid item xs={12} md={7}>
          <Card elevation={0}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom color="text.primary">
                Target Journal
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>
                Select the journal you're submitting to.
              </Typography>

              <FormControl fullWidth>
                <InputLabel>Select Journal</InputLabel>
                <Select
                  value={selectedJournal}
                  label="Select Journal"
                  onChange={(e) => onJournalChange(e.target.value)}
                >
                  {journals.map((journal) => (
                    <MenuItem key={journal.id} value={journal.id}>
                      <Box>
                        <Typography variant="body2" fontWeight={600}>
                          {journal.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {journal.abstract_max_words} word abstract limit
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {journalDetails && (
                <Box sx={{
                  mt: 2.5, p: 2,
                  border: '1px solid #C7D9FF',
                  borderRadius: '12px',
                  bgcolor: '#F8FAFF',
                }}>
                  <Typography variant="subtitle2" color="primary" gutterBottom fontWeight={700}>
                    {journalDetails.name} Guidelines
                  </Typography>

                  <Grid container spacing={1.5}>
                    {[
                      { label: 'Abstract Limit',   value: `${journalDetails.abstract_max_words} words` },
                      { label: 'Citation Style',    value: journalDetails.reference_style },
                      { label: 'Page Limit',        value: journalDetails.page_limit || 'No limit' },
                      { label: 'Font',              value: `${journalDetails.font}, ${journalDetails.font_size}pt` },
                      { label: 'Line Spacing',      value: journalDetails.line_spacing },
                    ].map(({ label, value }) => (
                      <Grid item xs={6} key={label}>
                        <Typography variant="caption" color="text.secondary" display="block">
                          {label}
                        </Typography>
                        <Typography variant="body2" fontWeight={600} color="text.primary">
                          {value}
                        </Typography>
                      </Grid>
                    ))}

                    {journalDetails.structure?.length > 0 && (
                      <Grid item xs={12}>
                        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.75 }}>
                          Required Structure
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.6 }}>
                          {journalDetails.structure.slice(0, 5).map((section, i) => (
                            <Chip
                              key={i}
                              label={section}
                              size="small"
                              sx={{
                                bgcolor: '#EEF3FF',
                                color: 'primary.main',
                                border: '1px solid #C7D9FF',
                                fontFamily: "'JetBrains Mono', monospace",
                                fontSize: 10,
                              }}
                            />
                          ))}
                          {journalDetails.structure.length > 5 && (
                            <Chip
                              label={`+${journalDetails.structure.length - 5} more`}
                              size="small"
                              sx={{
                                bgcolor: '#F4F7FC',
                                color: 'text.secondary',
                                border: '1px solid #E2EAF4',
                                fontSize: 10,
                              }}
                            />
                          )}
                        </Box>
                      </Grid>
                    )}
                  </Grid>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* ── Export Format Picker ── */}
        <Grid item xs={12} md={5}>
          <Card elevation={0} sx={{ height: '100%' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom color="text.primary">
                Export Format
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>
                Choose how you want to receive your formatted manuscript.
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {EXPORT_FORMATS.map((fmt) => {
                  const selected = exportFormat === fmt.id;
                  return (
                    <Box
                      key={fmt.id}
                      onClick={() => onExportFormatChange(fmt.id)}
                      sx={{
                        display: 'flex', alignItems: 'center', gap: 2,
                        p: 1.5, px: 2,
                        borderRadius: '12px',
                        border: '1.5px solid',
                        borderColor: selected ? 'primary.main' : '#E2EAF4',
                        bgcolor: selected ? '#EEF3FF' : '#F8FAFC',
                        cursor: 'pointer',
                        transition: 'all 0.14s',
                        '&:hover': {
                          borderColor: '#C7D9FF',
                          bgcolor: '#F4F7FF',
                        },
                      }}
                    >
                      <Typography sx={{ fontSize: 20 }}>{fmt.icon}</Typography>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="body2" fontWeight={700} color={selected ? 'primary.main' : 'text.primary'}>
                          {fmt.label}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {fmt.desc}
                        </Typography>
                      </Box>
                      {selected && (
                        <Box sx={{
                          width: 8, height: 8, borderRadius: '50%',
                          bgcolor: 'primary.main',
                        }} />
                      )}
                    </Box>
                  );
                })}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default JournalSelector;
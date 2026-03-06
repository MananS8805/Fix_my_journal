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
  Chip
} from '@mui/material';
import axios from 'axios';

const JournalSelector = ({ journals, selectedJournal, onJournalChange }) => {
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
      const response = await axios.get(`/journals/${journalId}`);
      if (response.data.success) {
        setJournalDetails(response.data.data);
      }
    } catch (error) {
      console.error('Error loading journal details:', error);
    }
  };

  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h5" gutterBottom>
        Select Target Journal
      </Typography>

      <FormControl fullWidth sx={{ mb: 3 }}>
        <InputLabel>Select Journal</InputLabel>
        <Select
          value={selectedJournal}
          label="Select Journal"
          onChange={(e) => onJournalChange(e.target.value)}
        >
          {journals.map((journal) => (
            <MenuItem key={journal.id} value={journal.id}>
              {journal.name} - {journal.abstract_max_words} word abstract
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {journalDetails && (
        <Card sx={{ mt: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {journalDetails.name} Guidelines
            </Typography>

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary">
                    Abstract
                  </Typography>
                  <Typography variant="body2">
                    Max {journalDetails.abstract_max_words} words
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary">
                    Citation Style
                  </Typography>
                  <Typography variant="body2">
                    {journalDetails.reference_style}
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary">
                    Page Limit
                  </Typography>
                  <Typography variant="body2">
                    {journalDetails.page_limit || 'No limit'}
                  </Typography>
                </Box>
              </Grid>

              <Grid item xs={12} sm={6}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary">
                    Font and Size
                  </Typography>
                  <Typography variant="body2">
                    {journalDetails.font}, {journalDetails.font_size}pt
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary">
                    Line Spacing
                  </Typography>
                  <Typography variant="body2">
                    {journalDetails.line_spacing}
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary">
                    Required Structure
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {journalDetails.structure.slice(0, 4).map((section, index) => (
                      <Chip
                        key={index}
                        label={section}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                    {journalDetails.structure.length > 4 && (
                      <Chip
                        label={`+${journalDetails.structure.length - 4} more`}
                        size="small"
                        variant="outlined"
                      />
                    )}
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default JournalSelector;

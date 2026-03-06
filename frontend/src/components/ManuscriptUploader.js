import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Typography,
  Paper,
  Button,
  LinearProgress,
  Alert,
  Chip,
} from '@mui/material';
import { CloudUpload, InsertDriveFile } from '@mui/icons-material';

const ManuscriptUploader = ({ onFileUpload, isProcessing, uploadedFile }) => {
  const onDrop = useCallback(
    (acceptedFiles) => {
      if (acceptedFiles.length > 0) onFileUpload(acceptedFiles[0]);
    },
    [onFileUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
    },
    multiple: false,
    disabled: isProcessing,
  });

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box sx={{ mb: 2 }}>
      {/* ── Drop zone ── */}
      <Paper
        {...getRootProps()}
        elevation={0}
        sx={{
          p: { xs: 4, sm: 6 },
          textAlign: 'center',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : '#C7D9FF',
          bgcolor: isDragActive ? '#EEF3FF' : '#F8FAFF',
          cursor: isProcessing ? 'not-allowed' : 'pointer',
          transition: 'all 0.18s ease',
          '&:hover': {
            borderColor: isProcessing ? '#C7D9FF' : 'primary.main',
            bgcolor: isProcessing ? '#F8FAFF' : '#EEF3FF',
          },
        }}
      >
        <input {...getInputProps()} />

        <Box sx={{
          width: 64, height: 64, borderRadius: '16px',
          bgcolor: '#EEF3FF',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          mx: 'auto', mb: 2,
        }}>
          <CloudUpload sx={{ fontSize: 30, color: 'primary.main' }} />
        </Box>

        <Typography variant="h6" fontWeight={600} color="text.primary" gutterBottom>
          {isDragActive ? 'Drop your manuscript here' : 'Drag and drop your manuscript'}
        </Typography>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>
          or click to browse files
        </Typography>

        <Typography variant="caption" color="text.disabled" display="block" sx={{ mb: 2 }}>
          Supported formats: PDF, DOCX, DOC
        </Typography>

        <Button
          variant="outlined"
          disabled={isProcessing}
          sx={{
            borderColor: '#C7D9FF',
            color: 'primary.main',
            '&:hover': { borderColor: 'primary.main', bgcolor: '#EEF3FF' },
          }}
        >
          Browse Files
        </Button>
      </Paper>

      {/* ── Processing indicator ── */}
      {isProcessing && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Processing manuscript…
          </Typography>
          <LinearProgress color="primary" sx={{ borderRadius: 4, height: 5 }} />
        </Box>
      )}

      {/* ── Uploaded file chip ── */}
      {uploadedFile && !isProcessing && (
        <Box sx={{ mt: 2 }}>
          <Alert
            severity="success"
            sx={{ mb: 1.5, bgcolor: '#F0FDF4', borderColor: '#BBF7D0', color: '#166534' }}
          >
            File uploaded successfully!
          </Alert>

          <Box sx={{
            display: 'flex', alignItems: 'center', gap: 1.5,
            p: 1.5, px: 2,
            bgcolor: '#F0F5FF',
            border: '1px solid #C7D9FF',
            borderRadius: '12px',
          }}>
            <InsertDriveFile sx={{ color: 'primary.main', fontSize: 22 }} />
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography variant="body2" fontWeight={600} color="text.primary" noWrap>
                {uploadedFile.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {formatFileSize(uploadedFile.size)}
              </Typography>
            </Box>
            <Chip
              label={uploadedFile.name.split('.').pop().toUpperCase()}
              size="small"
              sx={{
                bgcolor: '#EEF3FF',
                color: 'primary.main',
                border: '1px solid #C7D9FF',
                fontFamily: "'JetBrains Mono', monospace",
                fontWeight: 600,
              }}
            />
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default ManuscriptUploader;
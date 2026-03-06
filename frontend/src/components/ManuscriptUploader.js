import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Typography,
  Paper,
  Button,
  LinearProgress,
  Alert,
  Chip
} from '@mui/material';
import { CloudUpload, InsertDriveFile } from '@mui/icons-material';

const ManuscriptUploader = ({ onFileUpload, isProcessing, uploadedFile }) => {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      onFileUpload(acceptedFiles[0]);
    }
  }, [onFileUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc']
    },
    multiple: false,
    disabled: isProcessing
  });

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h5" gutterBottom>
        Upload Manuscript
      </Typography>

      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          textAlign: 'center',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          backgroundColor: isDragActive ? 'primary.50' : 'grey.50',
          cursor: isProcessing ? 'not-allowed' : 'pointer',
          transition: 'all 0.3s ease',
          '&:hover': {
            borderColor: isProcessing ? 'grey.300' : 'primary.main',
            backgroundColor: isProcessing ? 'grey.50' : 'primary.50'
          }
        }}
      >
        <input {...getInputProps()} />

        <CloudUpload
          sx={{
            fontSize: 64,
            color: isDragActive ? 'primary.main' : 'grey.400',
            mb: 2
          }}
        />

        <Typography variant="h6" gutterBottom>
          {isDragActive ? 'Drop your manuscript here' : 'Drag and drop your manuscript'}
        </Typography>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          or click to browse files
        </Typography>

        <Typography variant="body2" color="text.secondary">
          Supported formats: PDF, DOCX, DOC
        </Typography>

        <Button
          variant="outlined"
          sx={{ mt: 2 }}
          disabled={isProcessing}
        >
          Browse Files
        </Button>
      </Paper>

      {isProcessing && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" gutterBottom>
            Processing manuscript...
          </Typography>
          <LinearProgress />
        </Box>
      )}

      {uploadedFile && (
        <Box sx={{ mt: 2 }}>
          <Alert severity="success" sx={{ mb: 1 }}>
            File uploaded successfully!
          </Alert>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <InsertDriveFile color="primary" />
            <Box>
              <Typography variant="body1" fontWeight="medium">
                {uploadedFile.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {formatFileSize(uploadedFile.size)}
              </Typography>
            </Box>
            <Chip
              label={uploadedFile.name.split('.').pop().toUpperCase()}
              size="small"
              color="primary"
              variant="outlined"
            />
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default ManuscriptUploader;

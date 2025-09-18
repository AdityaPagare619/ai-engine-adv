import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';

interface Exam {
  id: string;
  name: string;
  description?: string;
}

interface ExamState {
  exams: Exam[];
  loading: boolean;
  error: string | null;
}

const initialState: ExamState = {
  exams: [],
  loading: false,
  error: null,
};

export const fetchExams = createAsyncThunk('exams/fetchAll', async () => {
  const response = await axios.get('/api/exams');
  return response.data;
});

const examSlice = createSlice({
  name: 'exams',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchExams.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchExams.fulfilled, (state, action: PayloadAction<Exam[]>) => {
        state.loading = false;
        state.exams = action.payload;
      })
      .addCase(fetchExams.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to fetch exams';
      });
  },
});

export default examSlice.reducer;

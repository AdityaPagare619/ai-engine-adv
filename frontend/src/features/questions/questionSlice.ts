import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { RootState } from '../../store/store';
import * as questionAPI from '../../api/questions';

// Types
export interface Question {
  id: string;
  title: string;
  content: string;
  type: 'multiple_choice' | 'numerical' | 'subjective' | 'match_following';
  difficulty: 'easy' | 'medium' | 'hard';
  subject: 'physics' | 'chemistry' | 'mathematics';
  topic: string;
  subtopic?: string;
  options?: QuestionOption[];
  correctAnswer: string | number | string[];
  explanation: string;
  imageUrl?: string;
  videoUrl?: string;
  marks: number;
  timeLimit?: number; // in seconds
  tags: string[];
  sourceExam?: string;
  year?: number;
  isVerified: boolean;
  verifiedBy?: string;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  statistics: QuestionStatistics;
}

export interface QuestionOption {
  id: string;
  text: string;
  imageUrl?: string;
  isCorrect: boolean;
}

export interface QuestionStatistics {
  totalAttempts: number;
  correctAttempts: number;
  averageTime: number;
  difficultyRating: number;
  reportCount: number;
}

export interface QuestionFilter {
  subject?: string[];
  difficulty?: string[];
  type?: string[];
  topics?: string[];
  tags?: string[];
  verified?: boolean;
  year?: number[];
  minMarks?: number;
  maxMarks?: number;
  searchQuery?: string;
}

export interface QuestionSort {
  field: 'difficulty' | 'marks' | 'createdAt' | 'statistics.totalAttempts';
  order: 'asc' | 'desc';
}

export interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface QuestionsState {
  questions: Question[];
  selectedQuestion: Question | null;
  loading: {
    fetchQuestions: boolean;
    fetchQuestion: boolean;
    createQuestion: boolean;
    updateQuestion: boolean;
    deleteQuestion: boolean;
    uploadImage: boolean;
  };
  errors: {
    fetchQuestions: string | null;
    fetchQuestion: string | null;
    createQuestion: string | null;
    updateQuestion: string | null;
    deleteQuestion: string | null;
    uploadImage: string | null;
  };
  filters: QuestionFilter;
  sort: QuestionSort;
  pagination: PaginationInfo;
  searchHistory: string[];
  recentlyViewed: string[];
  bookmarkedQuestions: string[];
  questionStats: {
    totalQuestions: number;
    questionsBySubject: Record<string, number>;
    questionsByDifficulty: Record<string, number>;
    verificationStatus: {
      verified: number;
      pending: number;
      rejected: number;
    };
  };
}

// Initial state
const initialState: QuestionsState = {
  questions: [],
  selectedQuestion: null,
  loading: {
    fetchQuestions: false,
    fetchQuestion: false,
    createQuestion: false,
    updateQuestion: false,
    deleteQuestion: false,
    uploadImage: false,
  },
  errors: {
    fetchQuestions: null,
    fetchQuestion: null,
    createQuestion: null,
    updateQuestion: null,
    deleteQuestion: null,
    uploadImage: null,
  },
  filters: {},
  sort: {
    field: 'createdAt',
    order: 'desc',
  },
  pagination: {
    page: 1,
    limit: 20,
    total: 0,
    totalPages: 0,
    hasNext: false,
    hasPrev: false,
  },
  searchHistory: JSON.parse(localStorage.getItem('questionSearchHistory') || '[]'),
  recentlyViewed: JSON.parse(localStorage.getItem('recentlyViewedQuestions') || '[]'),
  bookmarkedQuestions: JSON.parse(localStorage.getItem('bookmarkedQuestions') || '[]'),
  questionStats: {
    totalQuestions: 0,
    questionsBySubject: {},
    questionsByDifficulty: {},
    verificationStatus: {
      verified: 0,
      pending: 0,
      rejected: 0,
    },
  },
};

// Async thunks
export const fetchQuestions = createAsyncThunk(
  'questions/fetchQuestions',
  async (
    params: {
      filters?: QuestionFilter;
      sort?: QuestionSort;
      page?: number;
      limit?: number;
    } = {},
    { getState, rejectWithValue }
  ) => {
    try {
      const state = getState() as RootState;
      const currentFilters = params.filters || state.questions.filters;
      const currentSort = params.sort || state.questions.sort;
      const currentPage = params.page || state.questions.pagination.page;
      const currentLimit = params.limit || state.questions.pagination.limit;

      const response = await questionAPI.getQuestions({
        filters: currentFilters,
        sort: currentSort,
        page: currentPage,
        limit: currentLimit,
      });

      return {
        questions: response.questions,
        pagination: response.pagination,
        stats: response.stats,
        filters: currentFilters,
        sort: currentSort,
      };
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch questions');
    }
  }
);

export const fetchQuestionById = createAsyncThunk(
  'questions/fetchQuestionById',
  async (questionId: string, { rejectWithValue, dispatch }) => {
    try {
      const response = await questionAPI.getQuestion(questionId);

      // Add to recently viewed
      dispatch(addToRecentlyViewed(questionId));

      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch question');
    }
  }
);

export const createQuestion = createAsyncThunk(
  'questions/createQuestion',
  async (questionData: Omit<Question, 'id' | 'createdAt' | 'updatedAt' | 'statistics'>, { rejectWithValue }) => {
    try {
      const response = await questionAPI.createQuestion(questionData);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to create question');
    }
  }
);

export const updateQuestion = createAsyncThunk(
  'questions/updateQuestion',
  async (
    { id, updates }: { id: string; updates: Partial<Question> },
    { rejectWithValue }
  ) => {
    try {
      const response = await questionAPI.updateQuestion(id, updates);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to update question');
    }
  }
);

export const deleteQuestion = createAsyncThunk(
  'questions/deleteQuestion',
  async (questionId: string, { rejectWithValue }) => {
    try {
      await questionAPI.deleteQuestion(questionId);
      return questionId;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to delete question');
    }
  }
);

export const uploadQuestionImage = createAsyncThunk(
  'questions/uploadImage',
  async (
    { questionId, imageFile }: { questionId: string; imageFile: File },
    { rejectWithValue }
  ) => {
    try {
      const response = await questionAPI.uploadQuestionImage(questionId, imageFile);
      return { questionId, imageUrl: response.imageUrl };
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to upload image');
    }
  }
);

export const searchQuestions = createAsyncThunk(
  'questions/searchQuestions',
  async (
    { query, filters }: { query: string; filters?: QuestionFilter },
    { dispatch, rejectWithValue }
  ) => {
    try {
      // Add to search history
      dispatch(addToSearchHistory(query));

      const response = await questionAPI.searchQuestions(query, filters);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Search failed');
    }
  }
);

// Question slice
const questionSlice = createSlice({
  name: 'questions',
  initialState,
  reducers: {
    // Filter and sort actions
    setFilters: (state, action: PayloadAction<QuestionFilter>) => {
      state.filters = action.payload;
      state.pagination.page = 1; // Reset to first page when filters change
    },
    updateFilters: (state, action: PayloadAction<Partial<QuestionFilter>>) => {
      state.filters = { ...state.filters, ...action.payload };
      state.pagination.page = 1;
    },
    clearFilters: (state) => {
      state.filters = {};
      state.pagination.page = 1;
    },
    setSort: (state, action: PayloadAction<QuestionSort>) => {
      state.sort = action.payload;
      state.pagination.page = 1;
    },
    setPagination: (state, action: PayloadAction<Partial<PaginationInfo>>) => {
      state.pagination = { ...state.pagination, ...action.payload };
    },

    // Selected question actions
    setSelectedQuestion: (state, action: PayloadAction<Question | null>) => {
      state.selectedQuestion = action.payload;
    },
    clearSelectedQuestion: (state) => {
      state.selectedQuestion = null;
    },

    // Search and history actions
    addToSearchHistory: (state, action: PayloadAction<string>) => {
      const query = action.payload.trim();
      if (query && !state.searchHistory.includes(query)) {
        state.searchHistory.unshift(query);
        state.searchHistory = state.searchHistory.slice(0, 10); // Keep only last 10 searches
        localStorage.setItem('questionSearchHistory', JSON.stringify(state.searchHistory));
      }
    },
    clearSearchHistory: (state) => {
      state.searchHistory = [];
      localStorage.removeItem('questionSearchHistory');
    },
    addToRecentlyViewed: (state, action: PayloadAction<string>) => {
      const questionId = action.payload;
      const filtered = state.recentlyViewed.filter(id => id !== questionId);
      state.recentlyViewed = [questionId, ...filtered].slice(0, 20); // Keep only last 20
      localStorage.setItem('recentlyViewedQuestions', JSON.stringify(state.recentlyViewed));
    },
    clearRecentlyViewed: (state) => {
      state.recentlyViewed = [];
      localStorage.removeItem('recentlyViewedQuestions');
    },

    // Bookmark actions
    toggleBookmark: (state, action: PayloadAction<string>) => {
      const questionId = action.payload;
      const index = state.bookmarkedQuestions.indexOf(questionId);

      if (index > -1) {
        state.bookmarkedQuestions.splice(index, 1);
      } else {
        state.bookmarkedQuestions.push(questionId);
      }

      localStorage.setItem('bookmarkedQuestions', JSON.stringify(state.bookmarkedQuestions));
    },
    clearBookmarks: (state) => {
      state.bookmarkedQuestions = [];
      localStorage.removeItem('bookmarkedQuestions');
    },

    // Error handling
    clearError: (state, action: PayloadAction<keyof QuestionsState['errors']>) => {
      state.errors[action.payload] = null;
    },
    clearAllErrors: (state) => {
      Object.keys(state.errors).forEach(key => {
        state.errors[key as keyof QuestionsState['errors']] = null;
      });
    },

    // Question updates
    updateQuestionStatistics: (state, action: PayloadAction<{ questionId: string; stats: Partial<QuestionStatistics> }>) => {
      const { questionId, stats } = action.payload;
      const question = state.questions.find(q => q.id === questionId);
      if (question) {
        question.statistics = { ...question.statistics, ...stats };
      }
      if (state.selectedQuestion?.id === questionId) {
        state.selectedQuestion.statistics = { ...state.selectedQuestion.statistics, ...stats };
      }
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch questions cases
      .addCase(fetchQuestions.pending, (state) => {
        state.loading.fetchQuestions = true;
        state.errors.fetchQuestions = null;
      })
      .addCase(fetchQuestions.fulfilled, (state, action) => {
        state.loading.fetchQuestions = false;
        state.questions = action.payload.questions;
        state.pagination = action.payload.pagination;
        state.questionStats = action.payload.stats;
        state.filters = action.payload.filters;
        state.sort = action.payload.sort;
      })
      .addCase(fetchQuestions.rejected, (state, action) => {
        state.loading.fetchQuestions = false;
        state.errors.fetchQuestions = action.payload as string;
      })

      // Fetch single question cases
      .addCase(fetchQuestionById.pending, (state) => {
        state.loading.fetchQuestion = true;
        state.errors.fetchQuestion = null;
      })
      .addCase(fetchQuestionById.fulfilled, (state, action) => {
        state.loading.fetchQuestion = false;
        state.selectedQuestion = action.payload;
      })
      .addCase(fetchQuestionById.rejected, (state, action) => {
        state.loading.fetchQuestion = false;
        state.errors.fetchQuestion = action.payload as string;
      })

      // Create question cases
      .addCase(createQuestion.pending, (state) => {
        state.loading.createQuestion = true;
        state.errors.createQuestion = null;
      })
      .addCase(createQuestion.fulfilled, (state, action) => {
        state.loading.createQuestion = false;
        state.questions.unshift(action.payload);
        state.questionStats.totalQuestions += 1;
      })
      .addCase(createQuestion.rejected, (state, action) => {
        state.loading.createQuestion = false;
        state.errors.createQuestion = action.payload as string;
      })

      // Update question cases
      .addCase(updateQuestion.pending, (state) => {
        state.loading.updateQuestion = true;
        state.errors.updateQuestion = null;
      })
      .addCase(updateQuestion.fulfilled, (state, action) => {
        state.loading.updateQuestion = false;
        const index = state.questions.findIndex(q => q.id === action.payload.id);
        if (index !== -1) {
          state.questions[index] = action.payload;
        }
        if (state.selectedQuestion?.id === action.payload.id) {
          state.selectedQuestion = action.payload;
        }
      })
      .addCase(updateQuestion.rejected, (state, action) => {
        state.loading.updateQuestion = false;
        state.errors.updateQuestion = action.payload as string;
      })

      // Delete question cases
      .addCase(deleteQuestion.pending, (state) => {
        state.loading.deleteQuestion = true;
        state.errors.deleteQuestion = null;
      })
      .addCase(deleteQuestion.fulfilled, (state, action) => {
        state.loading.deleteQuestion = false;
        state.questions = state.questions.filter(q => q.id !== action.payload);
        if (state.selectedQuestion?.id === action.payload) {
          state.selectedQuestion = null;
        }
        state.questionStats.totalQuestions -= 1;
      })
      .addCase(deleteQuestion.rejected, (state, action) => {
        state.loading.deleteQuestion = false;
        state.errors.deleteQuestion = action.payload as string;
      })

      // Upload image cases
      .addCase(uploadQuestionImage.pending, (state) => {
        state.loading.uploadImage = true;
        state.errors.uploadImage = null;
      })
      .addCase(uploadQuestionImage.fulfilled, (state, action) => {
        state.loading.uploadImage = false;
        const { questionId, imageUrl } = action.payload;
        const question = state.questions.find(q => q.id === questionId);
        if (question) {
          question.imageUrl = imageUrl;
        }
        if (state.selectedQuestion?.id === questionId) {
          state.selectedQuestion.imageUrl = imageUrl;
        }
      })
      .addCase(uploadQuestionImage.rejected, (state, action) => {
        state.loading.uploadImage = false;
        state.errors.uploadImage = action.payload as string;
      })

      // Search questions cases
      .addCase(searchQuestions.fulfilled, (state, action) => {
        state.questions = action.payload.questions;
        state.pagination = action.payload.pagination;
      });
  },
});

// Actions
export const {
  setFilters,
  updateFilters,
  clearFilters,
  setSort,
  setPagination,
  setSelectedQuestion,
  clearSelectedQuestion,
  addToSearchHistory,
  clearSearchHistory,
  addToRecentlyViewed,
  clearRecentlyViewed,
  toggleBookmark,
  clearBookmarks,
  clearError,
  clearAllErrors,
  updateQuestionStatistics,
} = questionSlice.actions;

// Selectors
export const selectQuestions = (state: RootState) => state.questions.questions;
export const selectSelectedQuestion = (state: RootState) => state.questions.selectedQuestion;
export const selectQuestionsLoading = (state: RootState) => state.questions.loading;
export const selectQuestionsErrors = (state: RootState) => state.questions.errors;
export const selectQuestionFilters = (state: RootState) => state.questions.filters;
export const selectQuestionSort = (state: RootState) => state.questions.sort;
export const selectQuestionPagination = (state: RootState) => state.questions.pagination;
export const selectSearchHistory = (state: RootState) => state.questions.searchHistory;
export const selectRecentlyViewed = (state: RootState) => state.questions.recentlyViewed;
export const selectBookmarkedQuestions = (state: RootState) => state.questions.bookmarkedQuestions;
export const selectQuestionStats = (state: RootState) => state.questions.questionStats;

// Utility selectors
export const selectIsQuestionBookmarked = (questionId: string) => (state: RootState): boolean =>
  state.questions.bookmarkedQuestions.includes(questionId);

export const selectQuestionsBySubject = (subject: string) => (state: RootState): Question[] =>
  state.questions.questions.filter(q => q.subject === subject);

export const selectFilteredQuestionsCount = (state: RootState): number =>
  state.questions.pagination.total;

export default questionSlice.reducer;

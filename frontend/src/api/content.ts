import axios, { AxiosInstance, AxiosResponse } from 'axios';
import sanitizeHtml from 'sanitize-html';

export interface Question {
  question_id: string;
  question_text: string;
  question_number: string;
  subject_id: string;
  sheet_id: string;
  correct_option: string;
}

export interface QuestionOption {
  option_id: string;
  question_id: string;
  option_number: number;
  option_text: string;
  is_correct: boolean;
}

export interface QuestionWithOptions extends Question {
  options: QuestionOption[];
}

export interface QuestionsResponse {
  questions: QuestionWithOptions[];
  total: number;
  page: number;
  limit: number;
}

class ContentAPI {
  private client: AxiosInstance;
  private cache: Map<string, any> = new Map();

  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_CONTENT_API_URL || 'http://localhost:8002',
      timeout: 5000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for caching
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        // Cache successful responses
        if (response.config.method === 'get') {
          const cacheKey = `${response.config.url}_${JSON.stringify(response.config.params)}`;
          this.cache.set(cacheKey, {
            data: response.data,
            timestamp: Date.now(),
          });
        }
        return response;
      },
      (error) => {
        // Retry logic for network errors
        if (error.code === 'ECONNABORTED' || error.code === 'NETWORK_ERROR') {
          return this.client.request(error.config);
        }
        return Promise.reject(error);
      }
    );
  }

  private sanitizeContent(content: string): string {
    return sanitizeHtml(content, {
      allowedTags: ['p', 'br', 'strong', 'em', 'sub', 'sup', 'span'],
      allowedAttributes: {
        'span': ['class'],
      },
    });
  }

  // Mock API for now - will connect to actual backend
  async getQuestions(page = 1, limit = 10): Promise<QuestionsResponse> {
    try {
      // For now, we'll create a mock response based on our database data
      // In a real implementation, this would call the backend API
      const mockQuestions: QuestionWithOptions[] = [
        {
          question_id: 'SHT-PHY-001-Q-00001',
          question_number: '1',
          subject_id: 'EXM-2025-JEE_MAIN-001-SUB-PHY',
          sheet_id: 'SHT-PHY-001',
          question_text: this.sanitizeContent(
            'A uniform circular disc of radius R and mass M is rotating about an axis perpendicular to its plane and passing through its centre. A small circular part of radius R/2 is removed from the original disc as shown in the figure. Find the moment of inertia of the remaining part of the original disc about the axis as given above.'
          ),
          correct_option: '4',
          options: [
            {
              option_id: 'SHT-PHY-001-Q-00001-OPT-1',
              question_id: 'SHT-PHY-001-Q-00001',
              option_number: 1,
              option_text: '7/32 MR²',
              is_correct: false,
            },
            {
              option_id: 'SHT-PHY-001-Q-00001-OPT-2',
              question_id: 'SHT-PHY-001-Q-00001',
              option_number: 2,
              option_text: '9/32 MR²',
              is_correct: false,
            },
            {
              option_id: 'SHT-PHY-001-Q-00001-OPT-3',
              question_id: 'SHT-PHY-001-Q-00001',
              option_number: 3,
              option_text: '17/32 MR²',
              is_correct: false,
            },
            {
              option_id: 'SHT-PHY-001-Q-00001-OPT-4',
              question_id: 'SHT-PHY-001-Q-00001',
              option_number: 4,
              option_text: '13/32 MR²',
              is_correct: true,
            },
          ],
        },
        {
          question_id: 'SHT-PHY-001-Q-00002',
          question_number: '2',
          subject_id: 'EXM-2025-JEE_MAIN-001-SUB-PHY',
          sheet_id: 'SHT-PHY-001',
          question_text: this.sanitizeContent('Which law states F=ma?'),
          correct_option: '2',
          options: [
            {
              option_id: 'SHT-PHY-001-Q-00002-OPT-1',
              question_id: 'SHT-PHY-001-Q-00002',
              option_number: 1,
              option_text: 'First Law',
              is_correct: false,
            },
            {
              option_id: 'SHT-PHY-001-Q-00002-OPT-2',
              question_id: 'SHT-PHY-001-Q-00002',
              option_number: 2,
              option_text: 'Second Law',
              is_correct: true,
            },
            {
              option_id: 'SHT-PHY-001-Q-00002-OPT-3',
              question_id: 'SHT-PHY-001-Q-00002',
              option_number: 3,
              option_text: 'Third Law',
              is_correct: false,
            },
            {
              option_id: 'SHT-PHY-001-Q-00002-OPT-4',
              question_id: 'SHT-PHY-001-Q-00002',
              option_number: 4,
              option_text: 'Law of Gravitation',
              is_correct: false,
            },
          ],
        },
      ];

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 100));

      return {
        questions: mockQuestions,
        total: mockQuestions.length,
        page,
        limit,
      };
    } catch (error) {
      console.error('Error fetching questions:', error);
      throw error;
    }
  }

  async getQuestionById(questionId: string): Promise<QuestionWithOptions | null> {
    const response = await this.getQuestions();
    return response.questions.find(q => q.question_id === questionId) || null;
  }
}

export const contentAPI = new ContentAPI();
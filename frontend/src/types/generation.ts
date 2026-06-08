export type GenerationStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface CutVideo {
  id: string;
  status: GenerationStatus;
  video_url: string | null;
}

export interface CutImage {
  id: string;
  status: GenerationStatus;
  image_url: string | null;
  videos: CutVideo[];
}

export interface Cut {
  id: string;
  order: number;
  image_prompt: string;
  video_prompt: string;
  duration_sec: number;
  status: GenerationStatus;
  images: CutImage[];
}

export interface Generation {
  id: string;
  user_prompt: string;
  title: string | null;
  scenario: string | null;
  status: GenerationStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  cuts: Cut[];
}

export interface GenerationListItem {
  id: string;
  user_prompt: string;
  title: string | null;
  status: GenerationStatus;
  created_at: string;
}

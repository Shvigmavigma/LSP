// src/types/index.ts

export interface TeacherInfo {
  roles: string[];       
  curator: boolean;       
}

export type ProjectRole = 'customer' | 'supervisor' | 'expert' | 'executor' | 'curator';

export interface Participant {
  user_id: number;
  role: ProjectRole;
  joined_at?: string;
  invited_by?: number;
}

export interface User {
  id: number;
  nickname: string;
  fullname: string;
  class: number;
  speciality?: string;
  email: string;
  avatar?: string;
  is_active?: boolean;
  is_verified?: boolean;
  created_at?: string;
  updated_at?: string;
  is_teacher?: boolean;
  teacher_info?: TeacherInfo;
  is_admin?: boolean;
}

export interface SubTask {
  id: string;         
  title: string;
  description?: string;
  progressPercent: number; 
  completed: boolean;
}

// Новый интерфейс для обязательного файла
export interface RequiredFile {
  id: string;          // уникальный идентификатор в рамках задачи
  name: string;        // название требуемого файла
  description?: string; // описание (необязательно)
}

// Новый интерфейс для вложения (связь файла с задачей и, возможно, с обязательным требованием)
export interface TaskAttachment {
  id: string;               // уникальный ID вложения
  file_id: number;          // ID файла в таблице project_files
  required_file_id?: string; // ID обязательного файла, к которому привязано вложение
  uploaded_at: string;
  original_filename: string;
  mime_type: string;
  size: number;
}

export interface Task {
  id?: string;
  title: string;
  status: string;
  body: string;
  timeline?: string;
  timelinend?: string;
  progress?: number;
  subtasks?: SubTask[];
  comments?: Comment[];
  assigned_to?: number;
  requires_file?: boolean;       // устаревшее поле, оставлено для обратной совместимости
  required_files?: RequiredFile[];   // новое поле: список обязательных файлов
  attachments?: TaskAttachment[];    // новое поле: список прикреплённых файлов
}

export interface Comment {
  id: string;
  authorId: number;
  content: string;
  createdAt: string;
  isRead: boolean;
  hidden?: boolean;
  authorRole?: string;
}

export interface ProjectFile {
  id: number;
  filename: string;          // уникальное имя на диске
  original_filename: string;
  file_size: number;
  mime_type: string;
  uploaded_at: string;
  uploaded_by: number;
  task_id?: number | null;   // если null – файл привязан к проекту, иначе к задаче
  required_file_id?: string | null; // ID обязательного файла (если привязан к конкретному требованию)
}

export interface SuggestionComment {
  id: string;
  authorId: number;
  content: string;
  createdAt: string;
  isRead: boolean;
  hidden?: boolean;
}

export interface Suggestion {
  id: string;
  author_id: number;
  target_type: string;  // "project" | "task" | "link"
  target_id?: string;
  changes: Record<string, any>;
  status: 'pending' | 'accepted' | 'rejected';
  created_at: string;
  comments: SuggestionComment[];
}

export interface SuggestionCreate {
  target_type: string;
  target_id?: string;
  changes: Record<string, any>;
}

export interface Invitation {
  token: string;
  project_id: number;
  project_title: string;
  role: ProjectRole;
  invited_by: number;
  expires_at: string;
}

export interface JoinRequest {
  id: string;
  user_id: number;
  status: 'pending' | 'accepted' | 'rejected';
}

export interface Project {
  id: number;
  title: string;
  body: string;
  underbody: string;
  participants: Participant[];
  tasks: Task[];
  links?: ProjectLinks;
  comments?: Comment[];
  suggestions?: Suggestion[];
  join_requests?: JoinRequest[]; 
  is_hidden?: boolean;
  is_old: boolean;
  hidden_by?: number;  
}

export interface ProjectLinks {
  github?: string;
  google_drive?: string;
}

export type ProjectCreate = Omit<Project, 'id'>;

export interface ProjectUpdate {
  title?: string;
  body?: string;
  underbody?: string;
  tasks?: Task[];
  participants?: Participant[];
  links?: ProjectLinks;
  comments?: Comment[];
  is_old?: boolean;
}
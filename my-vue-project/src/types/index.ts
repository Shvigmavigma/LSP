// src/types/index.ts

export interface TeacherInfo {
  roles: string[];       
  curator: boolean;       
}

export type ProjectRole = 'customer' | 'supervisor' | 'expert' | 'executor' | 'curator';

// Типы для системы одобрения
export type ApprovalStatus = 'draft' | 'pending' | 'approved' | 'rejected';

export interface ApprovalInfo {
  is_approved: boolean;
  approval_status: ApprovalStatus;
  approval_requested_at: string | null;
  approval_requested_by: number | null;
  approval_handled_at: string | null;
  approval_handled_by: number | null;
  approval_comment: string | null;
}

export interface ApprovalRequestItem {
  project_id: number;
  project_title: string;
  requested_by: number | null;
  requested_by_name: string | null;
  requested_at: string | null;
  status: ApprovalStatus;
  customer_name: string | null;
}

export interface LifecycleStageState {
  id: string;
  status: 'pending' | 'current' | 'approval_pending' | 'completed' | 'rejected';
  requested_by?: number | null;
  requested_at?: string | null;
  handled_by?: number | null;
  handled_at?: string | null;
  comment?: string | null;
}

export interface ProjectLifecycleState {
  current_stage_id: string | null;
  stages: LifecycleStageState[];
}

export interface Participant {
  user_id: number;
  role: ProjectRole;
  joined_at?: string;
  invited_by?: number;
}

export interface User {
  id: number;
  display_name?: string | null;
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

  google_id?: string | null;
  oauth_providers?: string[];
}

export interface SubTask {
  id: string;         
  title: string;
  description?: string;
  progressPercent: number; 
  completed: boolean;
}

export interface RequiredFile {
  id: string;
  name: string;
  description?: string;
}

export interface TaskAttachment {
  id: string;
  file_id: number;
  required_file_id?: string;
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
  requires_file?: boolean;
  required_files?: RequiredFile[];
  attachments?: TaskAttachment[];
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
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  uploaded_at: string;
  uploaded_by: number;
  task_id?: number | null;
  required_file_id?: string | null;
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
  target_type: string;
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
  requested_role?: ProjectRole;
}

export interface Project {
  id: number;
  title: string;
  class_key?: string | null;
  direction_key?: string | null;
  body: string;
  underbody: string;
  participants: Participant[];
  tasks: Task[];
  links?: ProjectLinks;
  comments?: Comment[];
  lifecycle_state?: ProjectLifecycleState;
  file_quota_overrides?: Record<string, number>;
  suggestions?: Suggestion[];
  join_requests?: JoinRequest[]; 
  is_hidden?: boolean;
  is_old: boolean;
  hidden_by?: number;
  hidden_by_users?: number[];
  ignore_file_limits: boolean;
  required_roles?: Record<string, number>;
  is_approved?: boolean;
  approval_status?: string;
  approval_info?: ApprovalInfo; // Новое поле
}

export interface ProjectLinks {
  github?: string;
  google_drive?: string;
}

export type ProjectCreate = Omit<Project, 'id' | 'ignore_file_limits'> & Partial<Pick<Project, 'ignore_file_limits'>>;

export interface ProjectUpdate {
  title?: string;
  class_key?: string | null;
  direction_key?: string | null;
  body?: string;
  underbody?: string;
  tasks?: Task[];
  participants?: Participant[];
  links?: ProjectLinks;
  comments?: Comment[];
  is_old?: boolean;
}

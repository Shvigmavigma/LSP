declare module 'vue-ganttastic' {
  import { DefineComponent } from 'vue';
  export const GanttChart: DefineComponent<{
    tasks: any[];
    config?: any;
    onTaskUpdate?: (task: any) => void;
  }>;
}
import type { Task } from '@/types';

/**
 * Проверяет, уникально ли название задачи в списке.
 * @param tasks - список задач проекта
 * @param newTitle - новое название
 * @param excludeIndex - индекс задачи, которую нужно исключить из проверки (при редактировании)
 * @returns true, если название уникально
 */
export function isTaskTitleUnique(tasks: Task[], newTitle: string, excludeIndex?: number): boolean {
  const normalized = newTitle.trim().toLowerCase();
  return !tasks.some((task, idx) => {
    if (excludeIndex !== undefined && idx === excludeIndex) return false;
    return task.title.trim().toLowerCase() === normalized;
  });
}
import type { User } from '@/types';

export function formatFioMask(fullname?: string | null, fallback = ''): string {
  const parts = (fullname || '').trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return fallback || 'ID';
  const [surname, firstName, patronymic] = parts;
  const initials = [firstName, patronymic]
    .filter(Boolean)
    .map((part) => `${part.charAt(0).toUpperCase()}.`)
    .join(' ');
  return initials ? `${surname} ${initials}` : surname;
}

export function getUserDisplayName(user?: Pick<User, 'fullname' | 'email' | 'id'> | null): string {
  if (!user) return 'ID';
  return formatFioMask(user.fullname, user.email || `ID: ${user.id}`);
}

export function getUserInitial(user?: Pick<User, 'fullname' | 'email' | 'id'> | null): string {
  return getUserDisplayName(user).charAt(0).toUpperCase() || '?';
}

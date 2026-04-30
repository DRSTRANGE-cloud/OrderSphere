export type Product = {
  product_id: number;
  name: string;
  slug: string;
  description: string;
  price: number;
  stock: number;
  image_url: string;
  category?: string;
  rating?: number;
};

type ApiOptions = RequestInit & {
  body?: BodyInit | null;
};

export async function api<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const response = await fetch(path, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = typeof data.error === 'string' ? data.error : 'Request failed';
    throw new Error(message);
  }
  return data as T;
}

'use client';

import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { Bell, Eye, EyeOff, Lock, Mail, PackageCheck, Search, ShoppingCart, User } from 'lucide-react';
import { api, Product } from '@/lib/api';

type Me = { user: null | { username: string; email: string; role: string } };

export default function Home() {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [showPassword, setShowPassword] = useState(false);
  const [me, setMe] = useState<Me['user']>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    api<Me>('/api/auth/me').then((data) => setMe(data.user)).catch(() => null);
    api<{ products: Product[] }>('/api/products').then((data) => setProducts(data.products)).catch(() => null);
  }, []);

  async function submit(formData: FormData) {
    setError('');
    const body = Object.fromEntries(formData.entries());
    try {
      const path = mode === 'login' ? '/api/auth/login' : '/api/auth/signup';
      const result = await api<any>(path, { method: 'POST', body: JSON.stringify(body) });
      if (result.user) setMe(result.user);
      if (!result.user) setMode('login');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    }
  }

  if (!me) {
    return (
      <main className="grid min-h-screen lg:grid-cols-2">
        <section className="relative flex items-center justify-center overflow-hidden bg-[linear-gradient(135deg,rgba(3,34,88,.86),rgba(42,28,51,.82)),url('https://images.unsplash.com/photo-1468327768560-75b778cbb551?w=1400&q=80')] bg-cover bg-center p-8 text-center">
          <div className="max-w-xl card-enter">
            <img src="/logo.png" alt="OrderSphere" className="mx-auto mb-8 w-72 rounded-2xl bg-white shadow-2xl" />
            <h1 className="text-4xl font-black leading-tight tracking-normal md:text-6xl">Nature commerce, delivered with calm precision.</h1>
            <p className="mt-5 text-base text-white/75">Flowers, plants, gardening tools, seeds, fertilizers, and decorative greens in one polished SaaS workspace.</p>
          </div>
        </section>
        <section className="flex items-center justify-center p-6">
          <form action={submit} className="glass card-enter w-full max-w-md rounded-2xl p-8">
            <div className="mb-6 flex rounded-xl border border-white/10 bg-white/5 p-1">
              {(['login', 'signup'] as const).map((item) => (
                <button key={item} type="button" onClick={() => setMode(item)} className={`flex-1 rounded-lg px-4 py-2 text-sm font-bold transition ${mode === item ? 'bg-brandAccent text-white' : 'text-white/60'}`}>
                  {item === 'login' ? 'Login' : 'Signup'}
                </button>
              ))}
            </div>
            {mode === 'signup' && <Field icon={<User size={18} />} name="username" label="Username" />}
            <Field icon={<Mail size={18} />} name={mode === 'login' ? 'username' : 'email'} label={mode === 'login' ? 'Username or email' : 'Email'} />
            <div className="relative">
              <Field icon={<Lock size={18} />} name="password" label="Password" type={showPassword ? 'text' : 'password'} />
              <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-4 text-textSoft">
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            {error && <p className="mb-4 rounded-lg border border-red-400/30 bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}
            <button className="w-full rounded-xl bg-gradient-to-r from-grey to-midnightViolet px-5 py-3 font-black text-white shadow-lg shadow-black/30 transition hover:scale-[1.01] active:scale-[.98]">
              {mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen">
      <nav className="sticky top-0 z-10 border-b border-white/10 bg-jetBlack/80 px-6 py-4 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center gap-4">
          <PackageCheck className="text-textSoft" />
          <strong className="text-xl">Order<span className="text-brandAccent">Sphere</span></strong>
          <div className="ml-auto flex items-center gap-3 text-white/70"><Search size={19}/><Bell size={19}/><ShoppingCart size={19}/></div>
        </div>
      </nav>
      <section className="mx-auto max-w-7xl p-6">
        <div className="mb-8 grid gap-4 md:grid-cols-4">
          {['Role: ' + me.role, 'Products: ' + products.length, 'Fresh orders', 'Fast fulfilment'].map((label, i) => (
            <div key={label} className="glass card-enter rounded-xl p-5" style={{ animationDelay: `${i * 70}ms` }}>
              <PackageCheck className="mb-3 text-textSoft" /><p className="font-bold">{label}</p>
            </div>
          ))}
        </div>
        <div className="grid gap-5 md:grid-cols-3 lg:grid-cols-4">
          {products.map((product, i) => (
            <article key={product.product_id} className="glass card-enter overflow-hidden rounded-xl transition hover:-translate-y-1" style={{ animationDelay: `${i * 55}ms` }}>
              <img src={product.image_url} alt={product.name} className="h-44 w-full object-cover transition duration-500 hover:scale-105" loading="lazy" />
              <div className="p-4">
                <p className="text-xs font-bold uppercase tracking-widest text-textSoft">{product.category}</p>
                <h2 className="mt-2 font-black">{product.name}</h2>
                <p className="mt-2 line-clamp-2 text-sm text-white/60">{product.description}</p>
                <div className="mt-4 flex items-center justify-between">
                  <strong>Rs {Math.round(product.price)}</strong>
                  <span className="text-sm text-textSoft">{Number(product.rating || 0).toFixed(1)} star</span>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

function Field({ icon, name, label, type = 'text' }: { icon: ReactNode; name: string; label: string; type?: string }) {
  return (
    <label className="mb-4 flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3 focus-within:border-textSoft focus-within:ring-4 focus-within:ring-brandAccent/10">
      <span className="text-textSoft">{icon}</span>
      <input className="w-full bg-transparent text-sm outline-none placeholder:text-white/40" name={name} type={type} placeholder={label} required />
    </label>
  );
}


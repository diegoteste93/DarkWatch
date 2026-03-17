import { NextRequest, NextResponse } from 'next/server';

const protectedRoutes = ['/admin', '/dashboard'];

export function middleware(req: NextRequest) {
  const token = req.cookies.get('dw_token')?.value;
  const pathname = req.nextUrl.pathname;
  const isProtected = protectedRoutes.some((route) => pathname.startsWith(route));

  if (isProtected && !token) {
    return NextResponse.redirect(new URL('/login', req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/admin/:path*', '/dashboard/:path*']
};

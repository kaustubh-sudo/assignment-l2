import React from 'react';

export const useNavigate = () => jest.fn();
export const useLocation = () => ({ pathname: '/', state: null });
export const useParams = () => ({});
export const useSearchParams = () => [new URLSearchParams(), jest.fn()];
export const BrowserRouter = ({ children }) => <div data-testid="browser-router">{children}</div>;
export const MemoryRouter = ({ children, initialEntries }) => <div data-testid="memory-router">{children}</div>;
export const Routes = ({ children }) => <div>{children}</div>;
export const Route = ({ element }) => element;
export const Link = ({ children, to, ...props }) => <a href={to} {...props}>{children}</a>;
export const NavLink = ({ children, to, ...props }) => <a href={to} {...props}>{children}</a>;
export const Navigate = ({ to }) => null;
export const Outlet = () => null;

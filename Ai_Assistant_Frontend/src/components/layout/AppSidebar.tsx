import { NavLink, useLocation } from 'react-router-dom';
import { Home, FlaskConical, ChevronLeft, ChevronRight, Moon, Sun, TrendingUp } from 'lucide-react';
import { useAppStore } from '@/store/appStore';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from 'next-themes';

const navItems = [
  { path: '/', label: 'Home', icon: Home },
  { path: '/sandbox', label: 'Sandbox', icon: FlaskConical },
  { path: '/insights', label: 'Insights', icon: TrendingUp },
];

export function AppSidebar() {
  const { isSidebarCollapsed, toggleSidebar } = useAppStore();
  const location = useLocation();
  const { resolvedTheme, setTheme } = useTheme();

  const toggleTheme = () => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');
  };

  return (
    <motion.aside
      initial={false}
      animate={{ width: isSidebarCollapsed ? 64 : 220 }}
      transition={{ duration: 0.2, ease: 'easeInOut' }}
      className="h-screen bg-sidebar border-r border-sidebar-border flex flex-col shrink-0"
    >
      {/* Logo */}
      <div className="h-14 flex items-center justify-between px-4 border-b border-sidebar-border">
        <AnimatePresence mode="wait">
          {!isSidebarCollapsed ? (
            <motion.div
              key="full-logo"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <NavLink to="/" className="flex items-center gap-2">
                <img src="/analytix_logo.png" alt="Analytix" className="h-10 w-auto object-contain" />
              </NavLink>
            </motion.div>
          ) : (
            <motion.div
              key="icon-logo"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="mx-auto"
            >
              <NavLink to="/" className="w-8 h-8 flex items-center justify-center rounded-lg bg-primary/10 overflow-hidden">
                {/* For collapsed, likely just want the icon part or scaled down. 
                     Since I can't easily crop, I'll show the full logo scaled or fallback to an icon if provided. 
                     User said "change the logo", let's assuming the image works. 
                     If the image is wide, it might look small in 32px. 
                     I'll stick to a simple clean fit. */}
                <img src="/analytix_logo.png" alt="Analytix" className="h-full w-full object-cover" />
              </NavLink>
            </motion.div>
          )}
        </AnimatePresence>
        {!isSidebarCollapsed && (
          <button
            onClick={toggleTheme}
            className="p-1.5 rounded-lg hover:bg-sidebar-accent text-muted-foreground hover:text-foreground transition-colors"
            title={resolvedTheme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {resolvedTheme === 'dark' ? (
              <Sun className="w-4 h-4" />
            ) : (
              <Moon className="w-4 h-4" />
            )}
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200',
                    'text-sidebar-foreground hover:text-sidebar-accent-foreground',
                    'hover:bg-sidebar-accent',
                    isActive && 'bg-sidebar-accent text-sidebar-primary font-medium'
                  )}
                >
                  <item.icon className={cn(
                    'w-5 h-5 shrink-0',
                    isActive && 'text-primary'
                  )} />
                  <AnimatePresence>
                    {!isSidebarCollapsed && (
                      <motion.span
                        initial={{ opacity: 0, width: 0 }}
                        animate={{ opacity: 1, width: 'auto' }}
                        exit={{ opacity: 0, width: 0 }}
                        className="text-sm whitespace-nowrap overflow-hidden"
                      >
                        {item.label}
                      </motion.span>
                    )}
                  </AnimatePresence>
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Collapse Toggle */}
      <div className="p-3 border-t border-sidebar-border">
        <button
          onClick={toggleSidebar}
          className={cn(
            'w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg',
            'text-sidebar-foreground hover:text-sidebar-accent-foreground',
            'hover:bg-sidebar-accent transition-colors'
          )}
        >
          {isSidebarCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <>
              <ChevronLeft className="w-4 h-4" />
              <span className="text-xs">Collapse</span>
            </>
          )}
        </button>
      </div>
    </motion.aside>
  );
}

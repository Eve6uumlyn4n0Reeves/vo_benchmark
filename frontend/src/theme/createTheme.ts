import { createTheme as createMuiTheme, ThemeOptions } from '@mui/material/styles';
import { colors, typography, breakpoints, shadows } from './design-tokens';

declare module '@mui/material/styles' {
  interface Theme {
    customShadows: {
      card: string;
      dropdown: string;
      dialog: string;
    };
  }
  
  interface ThemeOptions {
    customShadows?: {
      card: string;
      dropdown: string;
      dialog: string;
    };
  }
}

export const createTheme = (mode: 'light' | 'dark') => {
  const isLight = mode === 'light';
  
  const baseTheme: ThemeOptions = {
    palette: {
      mode,
      primary: {
        main: colors.primary[700],
        light: colors.primary[400],
        dark: colors.primary[800],
        contrastText: '#ffffff',
      },
      secondary: {
        main: colors.secondary[500],
        light: colors.secondary[300],
        dark: colors.secondary[700],
        contrastText: '#ffffff',
      },
      error: {
        main: colors.error[500],
        light: colors.error[300],
        dark: colors.error[700],
        contrastText: '#ffffff',
      },
      warning: {
        main: colors.warning[500],
        light: colors.warning[300],
        dark: colors.warning[700],
        contrastText: 'rgba(0, 0, 0, 0.87)',
      },
      success: {
        main: colors.success[500],
        light: colors.success[300],
        dark: colors.success[700],
        contrastText: '#ffffff',
      },
      grey: colors.grey,
      background: {
        default: isLight ? colors.grey[50] : colors.grey[900],
        paper: isLight ? '#ffffff' : colors.grey[800],
      },
      text: {
        primary: isLight ? 'rgba(0, 0, 0, 0.87)' : '#ffffff',
        secondary: isLight ? 'rgba(0, 0, 0, 0.6)' : 'rgba(255, 255, 255, 0.7)',
        disabled: isLight ? 'rgba(0, 0, 0, 0.38)' : 'rgba(255, 255, 255, 0.5)',
      },
      divider: isLight ? 'rgba(0, 0, 0, 0.12)' : 'rgba(255, 255, 255, 0.12)',
    },
    typography: {
      fontFamily: typography.fontFamily.primary,
      h1: {
        fontSize: typography.fontSize['4xl'],
        fontWeight: typography.fontWeight.bold,
        lineHeight: typography.lineHeight.tight,
      },
      h2: {
        fontSize: typography.fontSize['3xl'],
        fontWeight: typography.fontWeight.bold,
        lineHeight: typography.lineHeight.tight,
      },
      h3: {
        fontSize: typography.fontSize['2xl'],
        fontWeight: typography.fontWeight.medium,
        lineHeight: typography.lineHeight.tight,
      },
      h4: {
        fontSize: typography.fontSize.xl,
        fontWeight: typography.fontWeight.medium,
        lineHeight: typography.lineHeight.normal,
      },
      h5: {
        fontSize: typography.fontSize.lg,
        fontWeight: typography.fontWeight.medium,
        lineHeight: typography.lineHeight.normal,
      },
      h6: {
        fontSize: typography.fontSize.base,
        fontWeight: typography.fontWeight.medium,
        lineHeight: typography.lineHeight.normal,
      },
      body1: {
        fontSize: typography.fontSize.base,
        fontWeight: typography.fontWeight.regular,
        lineHeight: typography.lineHeight.normal,
      },
      body2: {
        fontSize: typography.fontSize.sm,
        fontWeight: typography.fontWeight.regular,
        lineHeight: typography.lineHeight.normal,
      },
      caption: {
        fontSize: typography.fontSize.xs,
        fontWeight: typography.fontWeight.regular,
        lineHeight: typography.lineHeight.normal,
      },
      button: {
        fontSize: typography.fontSize.sm,
        fontWeight: typography.fontWeight.medium,
        textTransform: 'none',
      },
    },
    breakpoints: {
      values: breakpoints,
    },
    spacing: 8, // Base spacing unit (8px)
    shape: {
      borderRadius: 8,
    },
    shadows: [
      'none',
      shadows.sm,
      shadows.base,
      shadows.md,
      shadows.lg,
      shadows.xl,
      // Additional shadows for Material-UI
      '0 3px 5px -1px rgba(0,0,0,0.2),0 6px 10px 0 rgba(0,0,0,0.14),0 1px 18px 0 rgba(0,0,0,0.12)',
      '0 5px 5px -3px rgba(0,0,0,0.2),0 8px 10px 1px rgba(0,0,0,0.14),0 3px 14px 2px rgba(0,0,0,0.12)',
      '0 5px 6px -3px rgba(0,0,0,0.2),0 9px 12px 1px rgba(0,0,0,0.14),0 3px 16px 2px rgba(0,0,0,0.12)',
      '0 6px 6px -3px rgba(0,0,0,0.2),0 10px 14px 1px rgba(0,0,0,0.14),0 4px 18px 3px rgba(0,0,0,0.12)',
      '0 6px 7px -4px rgba(0,0,0,0.2),0 11px 15px 1px rgba(0,0,0,0.14),0 4px 20px 3px rgba(0,0,0,0.12)',
      '0 7px 8px -4px rgba(0,0,0,0.2),0 12px 17px 2px rgba(0,0,0,0.14),0 5px 22px 4px rgba(0,0,0,0.12)',
      '0 7px 8px -4px rgba(0,0,0,0.2),0 13px 19px 2px rgba(0,0,0,0.14),0 5px 24px 4px rgba(0,0,0,0.12)',
      '0 7px 9px -4px rgba(0,0,0,0.2),0 14px 21px 2px rgba(0,0,0,0.14),0 5px 26px 4px rgba(0,0,0,0.12)',
      '0 8px 9px -5px rgba(0,0,0,0.2),0 15px 22px 2px rgba(0,0,0,0.14),0 6px 28px 5px rgba(0,0,0,0.12)',
      '0 8px 10px -5px rgba(0,0,0,0.2),0 16px 24px 2px rgba(0,0,0,0.14),0 6px 30px 5px rgba(0,0,0,0.12)',
      '0 8px 11px -5px rgba(0,0,0,0.2),0 17px 26px 2px rgba(0,0,0,0.14),0 6px 32px 5px rgba(0,0,0,0.12)',
      '0 9px 11px -5px rgba(0,0,0,0.2),0 18px 28px 2px rgba(0,0,0,0.14),0 7px 34px 6px rgba(0,0,0,0.12)',
      '0 9px 12px -6px rgba(0,0,0,0.2),0 19px 29px 2px rgba(0,0,0,0.14),0 7px 36px 6px rgba(0,0,0,0.12)',
      '0 10px 13px -6px rgba(0,0,0,0.2),0 20px 31px 3px rgba(0,0,0,0.14),0 8px 38px 7px rgba(0,0,0,0.12)',
      '0 10px 13px -6px rgba(0,0,0,0.2),0 21px 33px 3px rgba(0,0,0,0.14),0 8px 40px 7px rgba(0,0,0,0.12)',
      '0 10px 14px -6px rgba(0,0,0,0.2),0 22px 35px 3px rgba(0,0,0,0.14),0 8px 42px 7px rgba(0,0,0,0.12)',
      '0 11px 14px -7px rgba(0,0,0,0.2),0 23px 36px 3px rgba(0,0,0,0.14),0 9px 44px 8px rgba(0,0,0,0.12)',
      '0 11px 15px -7px rgba(0,0,0,0.2),0 24px 38px 3px rgba(0,0,0,0.14),0 9px 46px 8px rgba(0,0,0,0.12)',
      '0 12px 16px -8px rgba(0,0,0,0.2),0 25px 40px 3px rgba(0,0,0,0.14),0 10px 48px 8px rgba(0,0,0,0.12)',
    ],
    customShadows: {
      card: shadows.base,
      dropdown: shadows.lg,
      dialog: shadows.xl,
    },
  };

  return createMuiTheme(baseTheme);
};

import { useCallback, useEffect } from 'react';

const SITE_KEY = import.meta.env.VITE_RECAPTCHA_SITE_KEY as string | undefined;
const SCRIPT_ID = 'recaptcha-v3';
const BADGE_VISIBLE_CLASS = 'recaptcha-in-use';

declare global {
    interface Window {
        grecaptcha?: {
            ready: (cb: () => void) => void;
            execute: (siteKey: string, options: { action: string }) => Promise<string>;
        };
    }
}

function loadScript(): void {
    if (!SITE_KEY || document.getElementById(SCRIPT_ID)) return;
    const script = document.createElement('script');
    script.id = SCRIPT_ID;
    script.src = `https://www.google.com/recaptcha/api.js?render=${SITE_KEY}`;
    script.async = true;
    document.head.appendChild(script);
}

/**
 * Returns a token getter. With no site key configured, or if the script cannot load, it resolves
 * to undefined and the request goes without a token: local development and tests must not depend
 * on reaching Google. The backend decides what a missing token means.
 */
export function useRecaptcha() {
    useEffect(() => {
        loadScript();
        document.body.classList.add(BADGE_VISIBLE_CLASS);
        return () => document.body.classList.remove(BADGE_VISIBLE_CLASS);
    }, []);

    return useCallback(async (action: string): Promise<string | undefined> => {
        if (!SITE_KEY) return undefined;

        const grecaptcha = window.grecaptcha;
        if (!grecaptcha) return undefined;

        try {
            return await new Promise<string>((resolve, reject) => {
                grecaptcha.ready(() => {
                    grecaptcha.execute(SITE_KEY, { action }).then(resolve, reject);
                });
            });
        } catch {
            return undefined;
        }
    }, []);
}

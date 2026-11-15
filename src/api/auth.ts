import { AuthenticationDetails, CognitoUser, CognitoUserPool } from "amazon-cognito-identity-js";

const pool = new CognitoUserPool({
  UserPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID as string,
  ClientId: import.meta.env.VITE_COGNITO_CLIENT_ID as string,
});

export function cognitoSignUp(email: string, password: string) {
  return new Promise<void>((resolve, reject) =>
    pool.signUp(email, password, [], [], (err) => (err ? reject(err) : resolve())));
}

export function cognitoConfirm(email: string, code: string) {
  return new Promise<void>((resolve, reject) =>
    new CognitoUser({ Username: email, Pool: pool }).confirmRegistration(code, true, (err) => (err ? reject(err) : resolve())));
}

export function cognitoLogin(email: string, password: string) {
  const user = new CognitoUser({ Username: email, Pool: pool });
  return new Promise<string>((resolve, reject) =>
    user.authenticateUser(new AuthenticationDetails({ Username: email, Password: password }), {
      onSuccess: (session) => resolve(session.getAccessToken().getJwtToken()),
      onFailure: reject,
    }));
}

export function cognitoAccessToken() {
  const user = pool.getCurrentUser();
  return new Promise<string | null>((resolve) => {
    if (!user) return resolve(null);
    user.getSession((err: Error | null, session: any) =>
      resolve(err || !session?.isValid() ? null : session.getAccessToken().getJwtToken()));
  });
}

export function cognitoLogout() {
  pool.getCurrentUser()?.signOut();
}

export function tokenExpiry(jwt: string): number {
  try { return JSON.parse(atob(jwt.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))).exp as number; }
  catch { return 0; }
}
/**
 * States
 * ======
 *
 * All section modules read from / write to this single object
 * so that circular import issues are avoided entirely.
 */

import type {
    AclRule,
    Backend,
    Cache,
    Frontend,
    HttpErrorGroup,
    ListenBlock,
    Mailer,
    Peer,
    Resolver,
    SslCertificate,
    UserProfile,
    Userlist,
    VersionStatus,
} from "./types";

export const state = {
    allFrontends: [] as Frontend[],
    allBackends: [] as Backend[],
    allAclRules: [] as AclRule[],
    allListenBlocks: [] as ListenBlock[],
    allUserlists: [] as Userlist[],
    allResolvers: [] as Resolver[],
    allPeers: [] as Peer[],
    allMailers: [] as Mailer[],
    allHttpErrors: [] as HttpErrorGroup[],
    allCaches: [] as Cache[],
    allSslCertificates: [] as SslCertificate[],
    cachedUserlists: null as Userlist[] | null,
    currentUser: null as UserProfile | null,
    versionStatus: null as VersionStatus | null,
};

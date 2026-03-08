/**
 * Entity type definitions
 * =======================
 */

/* Frontends  */

export interface FrontendBind {
    id: number;
    bind_line: string;
    sort_order?: number;
}

export interface FrontendOption {
    id: number;
    directive: string;
    value?: string;
    comment?: string;
    sort_order?: number;
    category?: string;
}

export interface Frontend {
    id: number;
    name: string;
    mode?: string;
    default_backend?: string | null;
    maxconn?: number | null;
    timeout_client?: string | null;
    timeout_http_request?: string | null;
    timeout_http_keep_alive?: string | null;
    timeout_queue?: string | null;
    option_forwardfor?: boolean;
    option_httplog?: boolean;
    option_tcplog?: boolean;
    compression_algo?: string | null;
    compression_type?: string | null;
    comment?: string | null;
    custom_options?: string | null;
    binds?: FrontendBind[];
    options?: FrontendOption[];
}

/* Backends  */

export interface BackendServer {
    id: number;
    name: string;
    address: string;
    port: number;
    weight?: number | null;
    maxconn?: number | null;
    maxqueue?: number | null;
    check_enabled?: boolean;
    ssl_enabled?: boolean;
    ssl_verify?: string | null;
    backup?: boolean;
    disabled?: boolean;
    inter?: string | null;
    fastinter?: string | null;
    downinter?: string | null;
    rise?: number | null;
    fall?: number | null;
    slowstart?: string | null;
    cookie_value?: string | null;
    send_proxy?: boolean;
    send_proxy_v2?: boolean;
    on_marked_down?: string | null;
    resolvers_ref?: string | null;
    resolve_prefer?: string | null;
    extra_params?: string | null;
    sort_order?: number;
}

export interface Backend {
    id: number;
    name: string;
    mode?: string;
    balance?: string;
    comment?: string | null;
    custom_options?: string | null;
    cookie?: string | null;
    health_check_enabled?: boolean;
    health_check_method?: string | null;
    health_check_uri?: string | null;
    http_check_expect?: string | null;
    option_forwardfor?: boolean;
    option_httplog?: boolean;
    option_tcplog?: boolean;
    option_redispatch?: boolean;
    retries?: number | null;
    retry_on?: string | null;
    http_reuse?: string | null;
    hash_type?: string | null;
    timeout_server?: string | null;
    timeout_connect?: string | null;
    timeout_queue?: string | null;
    compression_algo?: string | null;
    compression_type?: string | null;
    default_server_options?: string | null;
    errorfile?: string | null;
    extra_options?: string | null;
    auth_userlist?: string | null;
    servers?: BackendServer[];
}

/* ACL Rules  */

export interface AclRule {
    id: number;
    domain: string;
    acl_match_type?: string;
    frontend_id?: number | null;
    is_redirect?: boolean;
    backend_name?: string | null;
    redirect_target?: string | null;
    redirect_code?: number | null;
    enabled?: boolean;
    sort_order?: number;
    comment?: string | null;
}

/* Listen Blocks  */

export interface ListenBlockBind {
    id: number;
    bind_line: string;
    sort_order?: number;
}

export interface ListenBlock {
    id: number;
    name: string;
    mode?: string;
    balance?: string | null;
    maxconn?: number | null;
    timeout_client?: string | null;
    timeout_server?: string | null;
    timeout_connect?: string | null;
    default_server_params?: string | null;
    option_forwardfor?: boolean;
    option_httplog?: boolean;
    option_tcplog?: boolean;
    content?: string | null;
    comment?: string | null;
    binds?: ListenBlockBind[];
}

/* Userlists  */

export interface UserlistEntry {
    id: number;
    userlist_id?: number;
    username: string;
    password?: string;
    has_password?: boolean;
    sort_order?: number;
    groups?: string | null;
}

export interface Userlist {
    id: number;
    name: string;
    comment?: string | null;
    entries?: UserlistEntry[];
}

/* Resolvers  */

export interface Nameserver {
    id: number;
    name: string;
    address: string;
    port: number;
    sort_order?: number;
}

export interface Resolver {
    id: number;
    name: string;
    comment?: string | null;
    resolve_retries?: number | null;
    timeout_resolve?: string | null;
    timeout_retry?: string | null;
    hold_valid?: string | null;
    hold_nx?: string | null;
    hold_other?: string | null;
    hold_obsolete?: string | null;
    hold_timeout?: string | null;
    hold_refused?: string | null;
    hold_aa?: string | null;
    accepted_payload_size?: number | null;
    parse_resolv_conf?: number | null;
    extra_options?: string | null;
    nameservers?: Nameserver[];
}

/* Peers  */

export interface PeerEntry {
    id: number;
    name: string;
    address: string;
    port: number;
    sort_order?: number;
}

export interface Peer {
    id: number;
    name: string;
    comment?: string | null;
    default_bind?: string | null;
    default_server_options?: string | null;
    extra_options?: string | null;
    entries?: PeerEntry[];
}

/* Mailers  */

export interface MailerEntry {
    id: number;
    name: string;
    address: string;
    port: number;
    sort_order?: number;
    smtp_auth?: boolean;
    smtp_user?: string | null;
    has_smtp_password?: boolean;
    use_tls?: boolean;
    use_starttls?: boolean;
}

export interface Mailer {
    id: number;
    name: string;
    comment?: string | null;
    timeout_mail?: string | null;
    extra_options?: string | null;
    entries?: MailerEntry[];
}

/* HTTP Errors  */

export interface HttpErrorEntry {
    id: number;
    status_code: number;
    type: string;
    value: string;
    sort_order?: number;
}

export interface HttpErrorGroup {
    id: number;
    name: string;
    comment?: string | null;
    extra_options?: string | null;
    entries?: HttpErrorEntry[];
}

/* Caches  */

export interface Cache {
    id: number;
    name: string;
    total_max_size?: number | null;
    max_object_size?: number | null;
    max_age?: number | null;
    max_secondary_entries?: number | null;
    process_vary?: number | null;
    comment?: string | null;
    extra_options?: string | null;
}

/* SSL Certificates  */

export interface SslCertificate {
    id: number;
    domain: string;
    alt_domains?: string | null;
    email?: string | null;
    provider?: string;
    status?: string;
    cert_path?: string | null;
    key_path?: string | null;
    fullchain_path?: string | null;
    issued_at?: string | null;
    expires_at?: string | null;
    auto_renew?: boolean;
    challenge_type?: string;
    dns_plugin?: string | null;
    last_renewal_at?: string | null;
    last_error?: string | null;
    comment?: string | null;
}

/* Settings  */

export interface Setting {
    id: number;
    directive: string;
    value: string;
    type: string;
    sort_order?: number;
    comment?: string | null;
    category?: string;
}

/* Overview Stats  */

export interface OverviewStats {
    global_settings: number;
    default_settings: number;
    frontends: number;
    backends: number;
    backend_servers: number;
    acl_rules: number;
    listen_blocks: number;
    userlists: number;
    resolvers: number;
    peers: number;
    mailers: number;
    http_errors: number;
    caches: number;
    ssl_certificates: number;
    [key: string]: number;
}

/* User Profile  */

export interface UserProfile {
    id: number;
    name: string;
    email: string;
    created_at?: string;
}

/* Preset Types  */

export interface BindPreset {
    cat: string;
    line: string;
    h: string;
}

export interface FrontendOptionPreset {
    c: string;
    d: string;
    v: string;
    h: string;
}

export interface ListenPreset {
    name: string;
    mode: string;
    balance?: string;
    timeout_client?: string;
    timeout_server?: string;
    timeout_connect?: string;
    default_server_params?: string;
    option_forwardfor?: boolean;
    option_httplog?: boolean;
    option_tcplog?: boolean;
    content?: string;
    comment?: string;
    maxconn?: number;
}

export interface SettingPreset {
    d: string;
    v: string;
    h: string;
    c: string;
}

/* API Response Wrapper  */

export interface ApiListResponse<T> {
    items: T[];
}

/* Category Map  */

export interface CategoryDef {
    label: string;
}

/* Overview Stat Card  */

export interface StatCardItem {
    key: string;
    label: string;
    section: string;
    color: string;
    icon: string;
}

/* Flow Diagram Types  */

export interface FlowPoint {
    x: number;
    y: number;
}

/* Version Control Types  */

export interface VersionStatus {
    initialized: boolean;
    has_pending: boolean;
    pending_counts: Record<string, number>;
    current_hash: string | null;
    current_message: string | null;
    current_user_name: string | null;
    current_created_at: string | null;
}

export interface VersionSummary {
    hash: string;
    message: string;
    user_name: string;
    created_at: string;
    parent_hash: string | null;
}

export interface FieldChange {
    field: string;
    old: unknown;
    new: unknown;
}

export interface EntityUpdate {
    entity: string;
    entity_id?: string;
    old: Record<string, unknown>;
    new: Record<string, unknown>;
    changes: FieldChange[];
}

export interface SectionDiff {
    created: Record<string, unknown>[];
    deleted: Record<string, unknown>[];
    updated: EntityUpdate[];
    total: number;
}

export interface VersionDetail {
    hash: string;
    message: string;
    user_name: string;
    created_at: string;
    parent_hash: string | null;
    diff: Record<string, SectionDiff>;
}

export interface PendingChanges {
    has_pending: boolean;
    pending_counts: Record<string, number>;
    sections: Record<string, SectionDiff>;
}

export interface VersionListResponse {
    items: VersionSummary[];
    total: number;
}

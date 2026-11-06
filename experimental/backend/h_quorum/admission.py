"""Q_SURVIVAL_ONLY. Independently current deny-only guard profile, outside ABC/W."""
from h_quorum.common import Denied

def current_profile(cfg,namespace,actor):
    # Metadata-only core probes have synthetic actors, never admitted to SQL.
    # Supported application actors MUST use this controller-pinned profile.
    if actor.get('profile_required') is True:
        if namespace!=cfg.get('app_namespace') or actor['manifest']!=cfg.get('approved_manifest'):raise Denied('denied')

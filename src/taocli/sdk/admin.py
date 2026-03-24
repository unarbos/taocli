"""Admin SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Admin(SdkModule):
    """Admin (sudo) operations — set hyperparameters, raw sudo calls."""

    def set_tempo(self, netuid: int, tempo: int, sudo_key: str | None = None) -> Any:
        """Set the tempo (blocks per epoch) for a subnet."""
        cmd = ["admin", "set-tempo", "--netuid", str(netuid), "--tempo", str(tempo)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_max_validators(self, netuid: int, max: int, sudo_key: str | None = None) -> Any:
        """Set the maximum number of validators on a subnet."""
        cmd = ["admin", "set-max-validators", "--netuid", str(netuid), "--max", str(max)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_max_uids(self, netuid: int, max: int, sudo_key: str | None = None) -> Any:
        """Set the maximum number of UIDs on a subnet."""
        cmd = ["admin", "set-max-uids", "--netuid", str(netuid), "--max", str(max)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_immunity_period(self, netuid: int, period: int, sudo_key: str | None = None) -> Any:
        """Set the immunity period (epochs) for a subnet."""
        cmd = ["admin", "set-immunity-period", "--netuid", str(netuid), "--period", str(period)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_min_weights(self, netuid: int, min: int, sudo_key: str | None = None) -> Any:
        """Set the minimum number of weights per validator."""
        cmd = ["admin", "set-min-weights", "--netuid", str(netuid), "--min", str(min)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_max_weight_limit(self, netuid: int, limit: int, sudo_key: str | None = None) -> Any:
        """Set the maximum weight value per UID."""
        cmd = ["admin", "set-max-weight-limit", "--netuid", str(netuid), "--limit", str(limit)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_weights_rate_limit(self, netuid: int, limit: int, sudo_key: str | None = None) -> Any:
        """Set the rate limit for weight updates."""
        cmd = ["admin", "set-weights-rate-limit", "--netuid", str(netuid), "--limit", str(limit)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_commit_reveal(self, netuid: int, enabled: bool, sudo_key: str | None = None) -> Any:
        """Enable or disable commit-reveal for weights."""
        cmd = ["admin", "set-commit-reveal", "--netuid", str(netuid), "--enabled", str(enabled).lower()]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_difficulty(self, netuid: int, difficulty: int, sudo_key: str | None = None) -> Any:
        """Set the PoW difficulty for a subnet."""
        cmd = ["admin", "set-difficulty", "--netuid", str(netuid), "--difficulty", str(difficulty)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_activity_cutoff(self, netuid: int, cutoff: int, sudo_key: str | None = None) -> Any:
        """Set the activity cutoff (epochs) for a subnet."""
        cmd = ["admin", "set-activity-cutoff", "--netuid", str(netuid), "--cutoff", str(cutoff)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_default_take(self, take: int, sudo_key: str | None = None) -> Any:
        """Set the default delegate take percentage."""
        cmd = ["admin", "set-default-take", "--take", str(take)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_tx_rate_limit(self, limit: int, sudo_key: str | None = None) -> Any:
        """Set the global transaction rate limit."""
        cmd = ["admin", "set-tx-rate-limit", "--limit", str(limit)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_min_difficulty(self, netuid: int, difficulty: int, sudo_key: str | None = None) -> Any:
        """Set the minimum PoW difficulty for a subnet."""
        cmd = ["admin", "set-min-difficulty", "--netuid", str(netuid), "--difficulty", str(difficulty)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_max_difficulty(self, netuid: int, difficulty: int, sudo_key: str | None = None) -> Any:
        """Set the maximum PoW difficulty for a subnet."""
        cmd = ["admin", "set-max-difficulty", "--netuid", str(netuid), "--difficulty", str(difficulty)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_adjustment_interval(self, netuid: int, interval: int, sudo_key: str | None = None) -> Any:
        """Set the difficulty adjustment interval."""
        cmd = ["admin", "set-adjustment-interval", "--netuid", str(netuid), "--interval", str(interval)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_kappa(self, netuid: int, kappa: int, sudo_key: str | None = None) -> Any:
        """Set the kappa consensus parameter."""
        cmd = ["admin", "set-kappa", "--netuid", str(netuid), "--kappa", str(kappa)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_rho(self, netuid: int, rho: int, sudo_key: str | None = None) -> Any:
        """Set the rho consensus parameter."""
        cmd = ["admin", "set-rho", "--netuid", str(netuid), "--rho", str(rho)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_min_burn(self, netuid: int, burn: str, sudo_key: str | None = None) -> Any:
        """Set the minimum burn amount for registration."""
        cmd = ["admin", "set-min-burn", "--netuid", str(netuid), "--burn", burn]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_max_burn(self, netuid: int, burn: str, sudo_key: str | None = None) -> Any:
        """Set the maximum burn amount for registration."""
        cmd = ["admin", "set-max-burn", "--netuid", str(netuid), "--burn", burn]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_liquid_alpha(self, netuid: int, enabled: bool, sudo_key: str | None = None) -> Any:
        """Enable or disable liquid alpha on a subnet."""
        cmd = ["admin", "set-liquid-alpha", "--netuid", str(netuid), "--enabled", str(enabled).lower()]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_alpha_values(self, netuid: int, alpha_low: str, alpha_high: str, sudo_key: str | None = None) -> Any:
        """Set alpha low and high values for a subnet."""
        cmd = [
            "admin",
            "set-alpha-values",
            "--netuid",
            str(netuid),
            "--alpha-low",
            alpha_low,
            "--alpha-high",
            alpha_high,
        ]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_yuma3(self, netuid: int, enabled: bool, sudo_key: str | None = None) -> Any:
        """Enable or disable Yuma3 consensus."""
        cmd = ["admin", "set-yuma3", "--netuid", str(netuid), "--enabled", str(enabled).lower()]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_bonds_penalty(self, netuid: int, penalty: int, sudo_key: str | None = None) -> Any:
        """Set the bonds penalty for a subnet."""
        cmd = ["admin", "set-bonds-penalty", "--netuid", str(netuid), "--penalty", str(penalty)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_stake_threshold(self, threshold: str, sudo_key: str | None = None) -> Any:
        """Set the global stake threshold."""
        cmd = ["admin", "set-stake-threshold", "--threshold", threshold]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_network_registration(self, netuid: int, allowed: bool, sudo_key: str | None = None) -> Any:
        """Allow or disallow network registration on a subnet."""
        cmd = ["admin", "set-network-registration", "--netuid", str(netuid), "--allowed", str(allowed).lower()]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_pow_registration(self, netuid: int, allowed: bool, sudo_key: str | None = None) -> Any:
        """Allow or disallow PoW registration on a subnet."""
        cmd = ["admin", "set-pow-registration", "--netuid", str(netuid), "--allowed", str(allowed).lower()]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_adjustment_alpha(self, netuid: int, alpha: str, sudo_key: str | None = None) -> Any:
        """Set the difficulty adjustment alpha."""
        cmd = ["admin", "set-adjustment-alpha", "--netuid", str(netuid), "--alpha", alpha]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_subnet_moving_alpha(self, alpha: str, sudo_key: str | None = None) -> Any:
        """Set the global subnet moving alpha."""
        cmd = ["admin", "set-subnet-moving-alpha", "--alpha", alpha]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_mechanism_count(self, netuid: int, count: int, sudo_key: str | None = None) -> Any:
        """Set the number of mechanisms on a subnet."""
        cmd = ["admin", "set-mechanism-count", "--netuid", str(netuid), "--count", str(count)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_mechanism_emission_split(self, netuid: int, weights: str, sudo_key: str | None = None) -> Any:
        """Set the emission split between mechanisms."""
        cmd = ["admin", "set-mechanism-emission-split", "--netuid", str(netuid), "--weights", weights]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_nominator_min_stake(self, stake: str, sudo_key: str | None = None) -> Any:
        """Set the minimum stake for nominators."""
        cmd = ["admin", "set-nominator-min-stake", "--stake", stake]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def raw(self, call: str, args: str | None = None, sudo_key: str | None = None) -> Any:
        """Execute a raw sudo call."""
        cmd = ["admin", "raw", "--call", call]
        cmd += self._opt("--args", args)
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def list(self) -> Any:
        """List all admin-configurable parameters."""
        return self._run(["admin", "list"])

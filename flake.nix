# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

{
  description = "Toolchain for the mindclade .github repository";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        # nixos-25.05 is retained for a stable, already-locked base toolchain. Override only
        # actionlint so CI understands current GitHub Enterprise permission scopes such as
        # artifact-metadata without forcing an unrelated nixpkgs-wide upgrade.
        actionlintLatest = pkgs.buildGoModule.override { go = pkgs.go_1_25; } rec {
          pname = "actionlint";
          version = "1.7.12";
          src = pkgs.fetchFromGitHub {
            owner = "rhysd";
            repo = "actionlint";
            tag = "v${version}";
            hash = "sha256-mACSb3sYQtkijzk10mPi2ndy3zakonW1jlU7D/DV+SM=";
          };
          vendorHash = "sha256-bPhjeC6xcemV4KZx+Kc/Wbdz6Be6WsiolFTrJ7TURA0=";
          subPackages = [ "cmd/actionlint" ];
          ldflags = [
            "-s"
            "-w"
            "-X github.com/rhysd/actionlint.version=${version}"
          ];
        };
      in
      {
        # ---------------------------------------------------------------------------------
        # CI shell
        # ---------------------------------------------------------------------------------
        # This repository carried .github/actionlint.yaml and .yamllint.yaml for a while with
        # nothing that ran either of them: the configs described a standard, and no job
        # enforced it. Both are now invoked by the `lint` job in hygiene.yml, which is why
        # this shell exists at all — the repository is otherwise pure YAML and markdown and
        # needs no toolchain.
        #
        # The binaries come from the flake rather than from a release download so that the
        # repository defining the estate's supply-chain rules does not open a job by fetching
        # an unverified tarball. flake.lock pins the nixpkgs revision; Nix checks every store
        # path against its hash.
        devShells.ci = pkgs.mkShell {
          packages = with pkgs; [
            actionlintLatest
            gnumake
            python3
            shellcheck # actionlint shells out to it for `run:` blocks; absent, those go unchecked
            yamllint
          ];
        };

        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            actionlintLatest
            shellcheck
            yamllint
            yq-go
            jq
            gh
            gnumake
            pre-commit
            python3

            # bash 5. macOS ships 3.2, which lacks `declare -A` and `mapfile`.
            bashInteractive
          ];

          shellHook = ''
            echo ".github — org-wide governance and reusable workflows"
            echo
            echo "  actionlint         # what hygiene.yml runs"
            echo "  yamllint ."
            echo
            echo "  Reusable workflows here are consumed BY TAG (@v3.0.0). Changing one and"
            echo "  not cutting a tag changes nothing for any consumer."
          '';
        };
      });
}

# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

{
  description = "Toolchain for the mindclade .github repository";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  outputs =
    { nixpkgs, ... }:
    let
      # The shared-workflow repository is developed on Apple Silicon and executes on
      # Linux/amd64 in GitHub Actions. Keep the production-qualified native ARM systems
      # evaluable for consumers as well.
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
      ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      perSystem =
        system:
        let
          pkgs = import nixpkgs { inherit system; };

          # Keep this narrow override until nixpkgs supplies an actionlint release that
          # understands current GitHub Enterprise permission scopes such as artifact-metadata.
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
            meta = with pkgs.lib; {
              description = "Static checker for GitHub Actions workflow files";
              homepage = "https://github.com/rhysd/actionlint";
              license = licenses.mit;
              mainProgram = "actionlint";
              platforms = [ system ];
            };
          };
          python = pkgs.python3.withPackages (pythonPackages: [ pythonPackages.pyyaml ]);

          ciShell = pkgs.mkShell {
            packages = with pkgs; [
              actionlintLatest
              git
              gnumake
              python
              shellcheck
              yamllint
            ];
          };

          defaultShell = pkgs.mkShell {
            packages = with pkgs; [
              actionlintLatest
              shellcheck
              yamllint
              yq-go
              jq
              gh
              gnumake
              pre-commit
              python
              bashInteractive
            ];

            shellHook = ''
              echo ".github — org-wide governance and reusable workflows"
              echo
              echo "  actionlint         # what hygiene.yml runs"
              echo "  yamllint ."
              echo
              echo "  Reusable workflows here are consumed BY TAG (currently @v3.0.0). Changing one and"
              echo "  not cutting a tag changes nothing for any consumer."
            '';
          };
        in
        {
          inherit
            actionlintLatest
            ciShell
            defaultShell
            pkgs
            ;
        };
    in
    {
      packages = forAllSystems (system: {
        actionlint = (perSystem system).actionlintLatest;
      });

      devShells = forAllSystems (system: {
        ci = (perSystem system).ciShell;
        default = (perSystem system).defaultShell;
      });

      # `nix flake check` realizes the exact CI closure and the custom actionlint package;
      # repository validation then runs from that closure in hygiene.yml.
      checks = forAllSystems (system: {
        actionlint = (perSystem system).actionlintLatest;
        ci-shell = (perSystem system).ciShell;
      });

      formatter = forAllSystems (system: (perSystem system).pkgs.nixfmt);
    };
}

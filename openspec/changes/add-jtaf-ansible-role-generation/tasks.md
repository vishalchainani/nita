## 1. Project generator command

- [ ] 1.1 Add `generate-role` to `nitaprj.sh` with validation for project existence and required JTAF tooling.
- [ ] 1.2 Implement CLI parsing for `-p`, `-x`, `-t`, and optional `-v` arguments.
- [ ] 1.3 Run the upstream JTAF generator and capture output into a project-local role directory.

## 2. Profile and project skeleton

- [ ] 2.1 Add `profiles/jtaf-ansible/` with `project.yaml`, `ansible.cfg`, `hosts`, and `manifest`.
- [ ] 2.2 Include a base `build/sites.yaml` skeleton and `group_vars` placeholders for the generated role.
- [ ] 2.3 Ensure the generated project includes `filter_plugins` and `configs` directories.

## 3. Project lifecycle integration

- [ ] 3.1 Copy the generated role into the project and refresh project-local files on rerun.
- [ ] 3.2 Copy `jtaf_filters.py` into `filter_plugins/` and update the manifest.
- [ ] 3.3 Append the generated role to the build playbook and keep the change idempotent.
- [ ] 3.4 Include the trimmed schema and generated config output in the project artifact set.

## 4. Verification

- [ ] 4.1 Validate `nitaprj.sh create ... jtaf-ansible` creates a project skeleton correctly.
- [ ] 4.2 Run `nitaprj.sh generate-role <project>` against a sample YANG/XML input and confirm files are generated.
- [ ] 4.3 Verify the generated project builds and packages without breaking the existing generic flow.

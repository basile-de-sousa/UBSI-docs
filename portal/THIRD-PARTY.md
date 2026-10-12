# Portal dependency provenance

Exact transitive versions and distribution integrity checks are recorded in `requirements.lock` and `package-lock.json`. Python wheels include their upstream license files in the installed distributions. Base images include upstream OS/package notices. Retain them when redistributing the built image.

| Direct dependency | Version | License | Primary source |
| --- | --- | --- | --- |
| Django | 5.2.17 | BSD-3-Clause | https://www.djangoproject.com/ |
| Psycopg / binary distribution | 3.3.6 | LGPL-3.0-only; bundled libpq has its own PostgreSQL notice | https://www.psycopg.org/ |
| argon2-cffi | 25.1.0 | MIT | https://github.com/hynek/argon2-cffi |
| Gunicorn | 26.2.0 | MIT | https://gunicorn.org/ |
| WhiteNoise | 6.12.0 | MIT | https://whitenoise.readthedocs.io/ |
| HTMX | 2.0.11 | 0BSD | https://htmx.org/ |
| Tiptap core, StarterKit, tables, UniqueID and PM adapter | 3.31.3 | MIT | https://github.com/ueberdosis/tiptap |
| Vite (build only) | 8.3.4 | MIT | https://vite.dev/ |
| TypeScript (build only) | 7.0.2 | Apache-2.0 | https://www.typescriptlang.org/ |
| Python base image | 3.12.14 / Debian bookworm | PSF and included system package licenses | https://hub.docker.com/_/python |
| Node base image (build only) | 24.19.0 / Debian bookworm | MIT and included system package licenses | https://hub.docker.com/_/node |
| PostgreSQL image | 17.11 / Debian bookworm | PostgreSQL and included system package licenses | https://hub.docker.com/_/postgres |
| Mailpit image (development only, M2) | 1.31.5 | MIT | https://github.com/axllent/mailpit |

M3 adds the locally bundled Tiptap community editor and its ProseMirror dependencies. Every direct Tiptap package is pinned to 3.31.3; exact transitive versions and license metadata are in `package-lock.json`. No paid editor feature or external editor CDN is used. Integration references: [vanilla JavaScript](https://tiptap.dev/docs/editor/getting-started/install/vanilla-javascript), [UniqueID](https://tiptap.dev/docs/editor/extensions/functionality/uniqueid), [tables](https://tiptap.dev/docs/editor/extensions/nodes/table).

The build copies the full license notices of every locked non-development browser dependency into `static-built/THIRD-PARTY-NOTICES.txt`, collected and served with local static assets; it fails if a package's notice cannot be found. Retain that file when redistributing the build. M5 bundles the pinned document viewers (documents/assets.lock.json); M6 bundles pinned offline CPU model artifacts (search/assets.lock.json). Retain their upstream model cards and licenses when redistributing the image.

PostgreSQL 17.11 was selected against the [official version policy](https://www.postgresql.org/support/versioning/). Runtime patch versions and image digests must be deliberately updated together when security releases become available; a reproducible lock is not an automatic update mechanism.

Mailpit is an optional local SMTP sink, pinned by version and image digest in `compose.dev.yaml`. Its [official Docker documentation](https://mailpit.axllent.org/docs/install/docker/) defines ports 1025/8025. It does not run in the portal image, forward mail, or participate in production authentication. No new Python or browser dependency was added for M2.


## M6 offline retrieval

| Component | Pinned version/revision | License | Primary source |
| --- | --- | --- | --- |
| Sentence Transformers | 6.1.0 | Apache-2.0 | https://github.com/UKPLab/sentence-transformers |
| PyTorch CPU | 2.14.1 (Linux/Windows CPU wheel: 2.14.1+cpu) | BSD-3-Clause and bundled notices | https://pytorch.org/ |
| NumPy | 2.5.4 | BSD-3-Clause and bundled notices | https://numpy.org/ |
| multilingual-e5-small | 614241f622f53c4eeff9890bdc4f31cfecc418b3 | MIT, as declared by the upstream model card | https://huggingface.co/intfloat/multilingual-e5-small |
| mmarco-mMiniLMv2-L12-H384-v1 | 1427fd652930e4ba29e8149678df786c240d8825 | Apache-2.0, as declared by the upstream model card | https://huggingface.co/cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 |

`search/assets.lock.json` retains public origins and SHA-256 for all 17 acquired files, including upstream model cards. Acquisition verifies every file; runtime re-verifies before loading with `local_files_only=True`, `trust_remote_code=False` and offline/telemetry-disabled settings. The models receive only eligible published text inside the provided infrastructure. No inference-provider endpoint, paid service, generated business answer or private-data upload is used.

Usage contracts: [E5 prefixes/token limit](https://huggingface.co/intfloat/multilingual-e5-small), [offline Sentence Transformers loading](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html), [official PyTorch CPU installation](https://docs.astral.sh/uv/guides/integration/pytorch/). The hybrid selection policy is experimental; these software/model licenses do not constitute business qualification.

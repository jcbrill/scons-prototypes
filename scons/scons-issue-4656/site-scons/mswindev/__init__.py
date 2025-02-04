# SPDX-FileCopyrightText: Copyright 2025 Joseph C. Brill
# SPDX-License-Identifier: MIT

# minimal shim for pyargs

__all__ = [
    "platform_join_args",
    "platform_quote_arg",
    "platform_quote_args",
    "platform_split_args",
]

from .pyargs import (
    platform_join_args,
    platform_quote_arg,
    platform_quote_args,
    platform_split_args,
)
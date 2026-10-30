# User environment shared by Docker Sandbox shells and agent commands.

# Default shell and editor for interactive shell tools
# The shell workload's login shell is /bin/sh, but tmux uses SHELL when it
# creates a window. Use Bash so tmux loads the same interactive configuration
# as the main sandbox shell.
export SHELL=/bin/bash
export EDITOR=vim
export VISUAL=vim

if [ -n "${HOME-}" ]; then
	case ":${PATH-}:" in
		*:"$HOME/.local/bin":*) ;;
		*) PATH="$HOME/.local/bin${PATH:+:$PATH}" ;;
	esac

	case ":${PATH-}:" in
		*:"$HOME/bin":*) ;;
		*) PATH="$HOME/bin${PATH:+:$PATH}" ;;
	esac

	export PATH
fi

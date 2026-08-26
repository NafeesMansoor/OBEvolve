import * as React from 'react'

/**
 * State that resets to `initial` whenever `resetKey` changes — e.g. a
 * dependent dropdown's selection (course version) should clear when its
 * parent (course) changes. Implemented as a render-time adjustment (React's
 * documented pattern for "resetting state when a prop changes") rather than
 * `useEffect` + `setState`, which the repo's lint config (react-hooks
 * set-state-in-effect) flags as an anti-pattern since it causes an extra
 * render pass. See https://react.dev/learn/you-might-not-need-an-effect
 */
export function useResetOnChange<T>(
  resetKey: unknown,
  initial: T,
): [T, React.Dispatch<React.SetStateAction<T>>] {
  const [prevKey, setPrevKey] = React.useState(resetKey)
  const [state, setState] = React.useState(initial)

  if (prevKey !== resetKey) {
    setPrevKey(resetKey)
    setState(initial)
  }

  return [state, setState]
}

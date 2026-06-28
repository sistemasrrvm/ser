/**
 * Autocomplete Component
 * Campo de busca com dropdown de sugestões
 */

import { useState, useRef, useEffect } from 'react'
import { Input } from './input'

export interface AutocompleteOption {
  label: string
  value: any
}

interface AutocompleteProps {
  options: AutocompleteOption[]
  value?: any
  /** Label do valor selecionado (usado quando options ainda não foram carregadas) */
  selectedLabel?: string
  inputId?: string
  onChange: (value: any) => void
  placeholder?: string
  disabled?: boolean
  maxResults?: number
  totalCount?: number
  minCharsForSearch?: number
  onSearch?: (searchTerm: string) => void | Promise<void>
  onFocus?: () => void
}

const valuesMatch = (a: unknown, b: unknown) => String(a) === String(b)

export function Autocomplete({
  options,
  value,
  selectedLabel,
  inputId,
  onChange,
  placeholder = 'Digite para buscar...',
  disabled = false,
  maxResults = 50,
  totalCount = 0,
  minCharsForSearch = 1,
  onSearch,
  onFocus,
}: AutocompleteProps) {
  const [inputValue, setInputValue] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [filteredOptions, setFilteredOptions] = useState<AutocompleteOption[]>([])
  const [highlightedIndex, setHighlightedIndex] = useState(-1)
  const [isSearching, setIsSearching] = useState(false)
  const wrapperRef = useRef<HTMLDivElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const searchSeqRef = useRef(0)
  const onSearchRef = useRef(onSearch)
  onSearchRef.current = onSearch

  const requiresRemoteSearch = minCharsForSearch > 0 && totalCount > 50
  const searchTerm = inputValue.trim()
  const hasMinChars = searchTerm.length >= minCharsForSearch

  const selectedLabelFromOptions = value
    ? options.find((opt) => valuesMatch(opt.value, value))?.label
    : undefined
  const resolvedSelectedLabel = selectedLabelFromOptions || selectedLabel

  // Sincronizar input com valor selecionado (somente quando não está digitando)
  useEffect(() => {
    if (isEditing) return

    if (!value) {
      if (inputValue !== '') setInputValue('')
      return
    }

    if (resolvedSelectedLabel && inputValue !== resolvedSelectedLabel) {
      setInputValue(resolvedSelectedLabel)
    }
  }, [value, resolvedSelectedLabel, isEditing, inputValue])

  // Filtro local nas opções já carregadas
  useEffect(() => {
    if (searchTerm === '') {
      // Listas remotas: não reutilizar resultados da última busca com campo vazio
      if (requiresRemoteSearch) {
        setFilteredOptions([])
      } else {
        setFilteredOptions(options.slice(0, maxResults))
      }
    } else {
      const term = searchTerm.toLowerCase()
      setFilteredOptions(
        options.filter((opt) => opt.label.toLowerCase().includes(term)).slice(0, maxResults)
      )
    }
    setHighlightedIndex(-1)
  }, [searchTerm, options, maxResults, requiresRemoteSearch])

  // Busca remota com debounce (listas grandes)
  useEffect(() => {
    if (searchTimerRef.current) {
      clearTimeout(searchTimerRef.current)
      searchTimerRef.current = null
    }

    if (!onSearchRef.current || !requiresRemoteSearch || !hasMinChars) {
      setIsSearching(false)
      return
    }

    setIsSearching(true)
    const seq = ++searchSeqRef.current

    searchTimerRef.current = setTimeout(() => {
      const searchFn = onSearchRef.current
      if (!searchFn) {
        setIsSearching(false)
        return
      }
      void Promise.resolve(searchFn(searchTerm)).finally(() => {
        if (searchSeqRef.current === seq) {
          setIsSearching(false)
        }
      })
    }, 300)

    return () => {
      if (searchTimerRef.current) {
        clearTimeout(searchTimerRef.current)
        searchTimerRef.current = null
      }
    }
  }, [searchTerm, hasMinChars, requiresRemoteSearch])

  // Fechar dropdown ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setIsEditing(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setInputValue(newValue)
    setIsOpen(true)
    setIsEditing(true)

    if (newValue === '') {
      onChange('')
      setIsSearching(false)
      searchSeqRef.current += 1
      if (requiresRemoteSearch) {
        void Promise.resolve(onSearch?.(''))
      }
      return
    }

    // Usuário alterou texto após seleção — entrar em modo busca
    if (value && resolvedSelectedLabel && newValue !== resolvedSelectedLabel) {
      onChange('')
    }
  }

  const handleSelectOption = (option: AutocompleteOption) => {
    setInputValue(option.label)
    onChange(option.value)
    setIsOpen(false)
    setIsEditing(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        setIsOpen(true)
      }
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlightedIndex((prev) =>
          prev < filteredOptions.length - 1 ? prev + 1 : prev
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : 0))
        break
      case 'Enter':
        e.preventDefault()
        if (highlightedIndex >= 0 && highlightedIndex < filteredOptions.length) {
          handleSelectOption(filteredOptions[highlightedIndex])
        }
        break
      case 'Escape':
        setIsOpen(false)
        setHighlightedIndex(-1)
        break
    }
  }

  useEffect(() => {
    if (highlightedIndex >= 0 && dropdownRef.current) {
      const highlightedElement = dropdownRef.current.children[highlightedIndex] as HTMLElement
      if (highlightedElement) {
        highlightedElement.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
      }
    }
  }, [highlightedIndex])

  const showEmptyHint =
    isOpen &&
    searchTerm === '' &&
    requiresRemoteSearch

  const showSearching =
    isOpen &&
    searchTerm !== '' &&
    requiresRemoteSearch &&
    hasMinChars &&
    isSearching

  const showNoResults =
    isOpen &&
    searchTerm !== '' &&
    filteredOptions.length === 0 &&
    !showSearching &&
    (!requiresRemoteSearch || hasMinChars)

  return (
    <div ref={wrapperRef} className="relative">
      <Input
        id={inputId}
        type="text"
        value={inputValue}
        onChange={handleInputChange}
        onFocus={() => {
          setIsOpen(true)
          onFocus?.()
        }}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        autoComplete="off"
      />

      {isOpen && filteredOptions.length > 0 && !showSearching && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
        >
          {filteredOptions.map((option, index) => (
            <div
              key={`${option.value}-${index}`}
              className={`px-3 py-2 cursor-pointer text-sm ${
                index === highlightedIndex
                  ? 'bg-blue-100 text-blue-900'
                  : 'hover:bg-gray-100'
              }`}
              onClick={() => handleSelectOption(option)}
              onMouseEnter={() => setHighlightedIndex(index)}
            >
              {option.label}
            </div>
          ))}
        </div>
      )}

      {showSearching && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg p-3 text-sm text-gray-600 flex items-center gap-2">
          <span
            className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600"
            aria-hidden="true"
          />
          Buscando...
        </div>
      )}

      {showNoResults && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg p-3 text-sm text-gray-500">
          Nenhum resultado encontrado
        </div>
      )}

      {showEmptyHint && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg p-3 text-sm text-gray-600">
          Digite para buscar entre {totalCount} itens
        </div>
      )}
    </div>
  )
}
